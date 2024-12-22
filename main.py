import subprocess

def run_crawl(start_date, end_date, use_llm=False):
    try:
        print("Running crawl.py...")
        command = ["python", "crawl.py", "-s", start_date, "-e", end_date]
        if use_llm:
            command.append("-llm")
        subprocess.run(command, check=True)
        print("crawl.py completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error while running crawl.py: {e}")
        exit(1)

def run_train():
    try:
        print("Running train.py...")
        subprocess.run(["python", "train.py"], check=True)
        print("train.py completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error while running train.py: {e}")
        exit(1)
        
def run_browsing():
    try:
        print("Browsing Result...")
        subprocess.run(["python", "browsing/app.py"], check=True)
        print("app.py completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error while running train.py: {e}")
        exit(1)



def main():
    while True:
        task = input("Crawler(1), Browser(2) or Trainer(3)? (Type 1, 2, 3): ")
        if task == '1':
            start_date = input("please input the start date (in format 2024-12-22): ")
            end_date = input("please input the end date (in format 2024-12-22): ")
            use_llm = input("Use llm? (y/n): ")
            use_llm = True if use_llm == 'y' else False
            run_crawl(start_date, end_date, use_llm)
        elif task == '2':
            run_browsing()
        elif task == '3':
            run_train()
        else:
            print("Invalid input, type again.")


if __name__ == "__main__":
    main()