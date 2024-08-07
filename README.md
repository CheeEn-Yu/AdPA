# AdPA : Adaptive Paper Agent

![image](https://github.com/user-attachments/assets/b94e9a0c-50b2-4263-8e51-1a9e3045f0a2)


## Usage
You may change the research topic in crawl.py  
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

if you want to use this score dataset to fine-tune phi-3 agent, run
```bash
python train.py
```

## Future Feature
1. Dataloader for csv
2. Auto summarize paper by langchain with RAG (input PDF)
