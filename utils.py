import re
import os
import pprint
import textwrap
import torch 
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from datasets import Dataset, concatenate_datasets
from trl import SFTConfig, SFTTrainer, DataCollatorForCompletionOnlyLM
import peft
from peft import LoraConfig, get_peft_model, PeftConfig, PeftModel
from datasets import Dataset

def strip_all_lines(s: str) -> str:
    """Remove all leading and trailing spaces of each line in the string."""
    return '\n'.join([line.strip() for line in s.splitlines()])


class PaperAgent:
    def __init__(self, model_name="microsoft/Phi-3-mini-128k-instruct") -> None:
        self.model_name = model_name
        self.model = AutoModelForCausalLM.from_pretrained( 
            model_name,  
            device_map="auto",  
            torch_dtype="auto",  
            quantization_config=BitsAndBytesConfig(
                load_in_8bit=True,
                bnb_8bit_compute_dtype=torch.bfloat16,
                bnb_8bit_use_double_quant=True,
                bnb_8bit_quant_type='nf4'
            ),
            trust_remote_code=True,  
        )
        os.makedirs('./lora_model', exist_ok=True)
        if os.path.isfile('./lora_model/adapter_model.safetensors'):
            print('LoRA model exists. Loading model...')
            self.model = PeftModel.from_pretrained(self.model, './lora_model')

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        chat_template = textwrap.dedent(f'''
        You are a helpful AI assistant that good at reading and abstracting paper.
        Your task is to score the relevance (0~10) between the given paper, topics and briefly introduce the value of the research.
        output the response in json format:
        ```json
        "relevant score": 5/10
        ```
        Be sure to follow the json format.
        ''')
        self.messages = [
            {"role": "system", "content": strip_all_lines(chat_template)}, 
        ]
        self.chosen_topic = []
        self.generation_args = { 
            "max_new_tokens": 256, 
            "temperature": 0.01, 
            "do_sample": True, 
        }
        self.memory = {
            "prompt": [],
            "completion": []
        }

    def chat_with_history(self, input_str: str) -> str:
        self.messages.append(
            {"role": "user", "content": input_str}, 
        )
        token_sentence = self.tokenizer.apply_chat_template(self.messages, tokenize=False, add_generation_prompt=True)
        input_token = self.tokenizer(token_sentence, return_tensors='pt').to('cuda')
        output_token = self.model.generate(input_token['input_ids'], **self.generation_args)
        decode_output = self.tokenizer.batch_decode(output_token)
        output_list = decode_output[0].split('<|end|>')
        self.messages.append({"role": "assistant", "content": output_list[-2].replace("<|assistant|>", "")})

        return output_list[-2]
    
    @torch.no_grad()
    def chat(self, input_str: str, save_memory=False) -> str:
        token_sentence = self.tokenizer.apply_chat_template(self.messages+[{"role": "user", "content": input_str}], tokenize=False, add_generation_prompt=True)
        input_token = self.tokenizer(token_sentence, return_tensors='pt').to('cuda')
        output_token = self.model.generate(**input_token, **self.generation_args)
        decode_output = self.tokenizer.batch_decode(output_token)
        output_list = decode_output[-1].split('<|assistant|>')

        if save_memory:
            self.memory['prompt'].append(decode_output[0].split('<|end|>')[1].replace('<|user|>', ''))
            self.memory['completion'].append(decode_output[0].split('<|assistant|>')[-1])

        return output_list[-1].replace('<|end|>', '')
    
    def get_score(self, crawl_paper):
        '''
        result = {
            "paper id": paperId,
            "abstract url": abstractUrl,
            "title": title,
            "rating": str(rating).replace(".0", ""),
            "keywords": keywords,
            "abstract": abstract,
            "subjects": subjects,
            "comment": comment
        }
        '''
        paper_prompt = textwrap.dedent(f'''
        topic:{self.chosen_topic}
        paper title: {crawl_paper['title']}
        paper abstract: {crawl_paper['abstract']}
        ''')
        raw_comment = self.chat(paper_prompt)
        pattern = r'"relevant[_ ]score":\s*(\d+)(?:/\d+)?'
        match = re.search(pattern, raw_comment)
        if match:
            score = match.group(1)
        else:
            pprint.pp(raw_comment)
            score = 0
        return score, raw_comment

    def add_topic(self, chosen_topic: str):
        self.chosen_topic.append(chosen_topic)

    @staticmethod
    def formatting_prompts_func(example):
        output_texts = []
        for i in range(len(example['prompt'])):
            text = f"<|user|> {example['prompt'][i]}\n <|assistant|>{example['completion'][i]}"
            output_texts.append(text)
        return output_texts
    
    def update(self, dataset: Dataset):
        if isinstance(self.model, peft.peft_model.PeftModelForCausalLM):
            self.model.unload()
            # lora_config = PeftConfig.from_pretrained("./lora_model")
            self.model = PeftModel.from_pretrained(self.model, './lora_model', is_trainable=True)
        response_template = "<|assistant|>"
        collator = DataCollatorForCompletionOnlyLM(response_template, tokenizer=self.tokenizer)
        peft_config = LoraConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["qkv_proj"],
        )
        training_args = SFTConfig(
            output_dir='./',
            per_device_train_batch_size=1,
            num_train_epochs=3,
            gradient_accumulation_steps=8,
            gradient_checkpointing=False,
            learning_rate=2e-4,
            optim="paged_adamw_8bit",
            logging_steps = 1,
            warmup_ratio = 0.1,
            report_to = 'none'
        )
        trainer = SFTTrainer(
            model=self.model,
            train_dataset=dataset,
            args=training_args,
            formatting_func=PaperAgent.formatting_prompts_func,
            data_collator=collator,
            peft_config=peft_config,
        )
        trainer.train()
        print('Saving model...')
        self.model.save_pretrained('./lora_model')

    def reset(self):
        del self.model
        torch.cuda.empty_cache()
        self.model = AutoModelForCausalLM.from_pretrained( 
            self.model_name,  
            device_map="auto",  
            torch_dtype="auto",  
            quantization_config=BitsAndBytesConfig(
                load_in_8bit=True,
                bnb_8bit_compute_dtype=torch.bfloat16,
                bnb_8bit_use_double_quant=True,
                bnb_8bit_quant_type='nf4'
            ),
            trust_remote_code=True,  
        )
    def format_paper_prompt(self, crawl_paper):
        return textwrap.dedent(f'''
            topic: {self.chosen_topic}
            paper title: {crawl_paper['Title']}
            paper abstract: {crawl_paper['Abstract']}
            score: {crawl_paper['Score']}
        ''')

    def add_topic(self, chosen_topic: str):
        self.chosen_topic.append(chosen_topic)
    
    @staticmethod
    def template_score(score: int) -> str:
        return f'relevance score: {str(score)}/10'



class Rater:
    def __init__(self):
        """
        the rating of subject will only be count once i.e., paper with multiple
        matched subject will only get the rating of the highest rated subject
        
        You can fine all categories on https://arxiv.org/category_taxonomy
        """
        self.SubjectOfInterest = {
            1: [
                # "cs.CL",    # Computation and Language
                # "cs.SD",    # Sound 
                # "eess.AS",  # Audio and Speech Processing
                # "cs.IR",    # Information Retrieval
                "cs.MA",    # Multiagent Systems
                "cs.CV",    # Computer Vision and Pattern Recognition
                "eess.IV",  # Image and Video Processing
                "cs.AR",
                "cs.GR",
                "cs.IT",
                "cs.LG",
                "cs.MM"
                
            ],
            0.5: [
                "cs.AI",    # Artificial Intelligence
                "cs.LG",    # Machine Learning
                # "cs.SI",    # Social and Information Networks
                # "cs.CY"     # Computers and Society
            ]
        }

        """
        the rating of phrase will be count accumulatively i.e., paper will get
        sum of all rating of matched phrases (set)
        """
        self.PhraseOfInterest = {
            -2: [
                ["Chemistry"], ["Biology"], ["Deep Learning"]
            ],
            -1: [
                ["Social"], ["speech"]
            ],
            1: [
                ["Green Learning"]
            ]
            # 0.5: [
            #     ["Agent"], ["TTA"] , ["ASR"], ["Speech Recognition"]
            # ],
            # 1: [
            #     ["RAG"], ["Test-time-adaptation"], ["Continual learning"], ["whisper"]
            # ]
        }

        """
        the rating of conference will only be count once
        """
        self.ConferenceOfInterest = {
            0.5: [
                "AAAI", "ECCV", "EMNLP", "ICASSP", "ICCV", "ICLR",
                "Interspeech", "NeurIPS", "NIPS", "WACV", "ICML", "CVPR"
            ],
            1: [
                "APSIPA"
            ]
            # CVPR
        }

    
    def matchOnce(self, ratingDict, content):
        keywords = []
        finalRating = 0
        
        for rating in sorted(ratingDict.keys()):
            for keyword in ratingDict[rating]:
                if (keyword in content):
                    keywords.append(keyword)
                    if (rating > finalRating):
                        finalRating = rating
        
        if (len(keywords) > 0): keywords = [keywords]
        
        return finalRating, keywords
    

    def matchAll(self, ratingDict, content):
        keywords = []
        finalRating = 0

        for (rating, phrasesGroup) in sorted(ratingDict.items(), reverse = True):
            for phrases in phrasesGroup:
                matches = []

                for phrase in phrases:
                    phrase = r"\b" + phrase + r"\b"
                    m = re.search(phrase, content, flags = re.IGNORECASE)
                    if (m != None): matches.append(m.group(0))

                if (len(matches) > 0):
                    finalRating += rating
                    keywords.append(matches)
        
        return finalRating, keywords


    def __call__(self, title, subjects, abstract, comment):
        cntRating, cntKeywords = self.matchAll(self.PhraseOfInterest, title + " " + abstract)
        sbjRating, sbjKeywords = self.matchOnce(self.SubjectOfInterest, subjects)

        if (comment != None):
            cmtRating, cmtKeywords = self.matchOnce(self.ConferenceOfInterest, comment)
        else:
            cmtRating, cmtKeywords = 0, []

        keywords = cntKeywords + sbjKeywords + cmtKeywords
        rating = (cntRating + sbjRating + cmtRating) if (len(keywords) != 0) else -10
        
        return rating, keywords

rater = Rater()
