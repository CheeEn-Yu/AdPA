import textwrap
from datasets import load_dataset
from utils import PaperAgent
import warnings
warnings.filterwarnings("ignore")


# def format_paper_prompt(crawl_paper, chosen_topic):
#     return textwrap.dedent(f'''
#         topic: {chosen_topic}
#         paper title: {crawl_paper['Title']}
#         paper abstract: {crawl_paper['Abstract']}
#         ''')

def format_dataset(example):
    example['prompt'] = textwrap.dedent(f'''
        topic: {example['Topic']}
        paper title: {example['Title']}
        paper abstract: {example['Abstract']}
        ''')

    example['completion'] = f'```json\n{{\n  \"relevant score\": {example["Score"]}/10\n\}}\n```'  # Assuming 'completion' is the 'Abstract'
    return example


if __name__ == '__main__':
    agent = PaperAgent()
    dataset = load_dataset('csv', data_files='./human_scores.csv')
    dataset = dataset.map(lambda example: format_dataset(example))
    dataset = dataset.remove_columns(['Date', 'Paper ID', 'Title', 'Score', 'Abstract', 'Topic'])
    print(dataset)
    agent.update(dataset['train'])
    