# AdPA : Adaptive Paper Agent
Paper Agent is an AI Agent designed to assist in reading the latest research papers, filtering and identifying those that are relevant and valuable to your research focus.

![image](https://github.com/user-attachments/assets/b94e9a0c-50b2-4263-8e51-1a9e3045f0a2)


## Environment

Install the necessary modules before running the code.
```bash
pip install requirements.txt
```


## Get Started

In the `__init__()` method of utils.py Rater(), set the interest arXiv topics, conferences, and keywords. 
Then, modify the research topic in crawl.py to allow the LLM to assess relevance.
then run
```bash
# -s for start date, -e for end date
python crawl.py -s 2024-07-01 -e 2024-07-05
```
then program will parse the paper betweeen the date and save the result into results/

For visualization, run
```bash
python browsing/app.py
```
you can score the paper, it would save into human_scores.csv.

if you want to fine-tune phi-3 agent with your score dataset, run
```bash
python train.py
```
Or simply run:
```bash
python main.py
```

Follow the instruction and fill in the command.

## Future Feature
1. Fine-tune with reflect data
2. Auto summarize paper by langchain with RAG (input PDF)
