import os
import openai
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Set your OpenAI API key here or load it from environment variables
openai.api_key = os.environ.get('OPENAI_KEY')

def get_repos(username):
    response = requests.get(repo["clone_url"] + "/archive/master.zip")
    return response.json()

def preprocess_code(repo):
    try:
        response = requests.get(repo["clone_url"] + "/archive/master.zip")
        
        code_data = response.content.decode("utf-8")
        code_filename = repo["name"] + ".zip"
        localStorage_key = "code_" + repo["name"]
        localStorage_key_filename = "filename_" + repo["name"]
        
        if not hasattr(app, 'localStorage'):
            app.localStorage = {}
        app.localStorage[localStorage_key] = code_data
        app.localStorage[localStorage_key_filename] = code_filename
        
        return code_filename

    except PermissionError:
        print("Permission denied when accessing the repo directory")
        return None

def get_complexity(files):
    try:
        prompt = "Analyze this code and describe its complexity: \n\n{'\n\n'.join(files)}"
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt,
            max_tokens=1000
        )

        return response.choices[0].text

    except openai.error.RateLimitError:
        print("Hit OpenAI rate limit")
        return "Rate limited"

def print_repo(repo):
    return (
    "Repository: " + repo['name'] + "\n" +
    "Owner: " + repo['owner']['login'] + "\n" +
    "Stars: " + str(repo['stargazers_count']) + "\n" +
    "Forks: " + str(repo['forks_count']) + "\n" +
    "Open Issues: " + str(repo['open_issues']) + "\n" +
    "Language: " + repo['language'] + "\n"
     )


def get_most_complex(username):
    repos = get_repos(username)
    complexity_scores = []

    for repo in repos:
        files = preprocess_code(repo)
        complexity = get_complexity(files)
        complexity_scores.append((repo, complexity))

    most_complex = max(complexity_scores, key=lambda x: len(x[1]))
    return most_complex

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        most_complex = get_most_complex(username)
        return render_template('result.html', username=username, most_complex=most_complex)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
