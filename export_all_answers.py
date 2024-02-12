import requests
import json
from types import SimpleNamespace
from weasyprint import HTML
import openai
openai.api_key = "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"
import re
import html
baseJSON = {
    "operationName": "questionData",
    "variables": {
        "titleSlug": "PLACEHOLDER"
    },
    "query": "query questionData($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    questionId\n    questionFrontendId\n    boundTopicId\n    title\n    titleSlug\n    content\n    translatedTitle\n    translatedContent\n    isPaidOnly\n    difficulty\n    likes\n    dislikes\n    isLiked\n    similarQuestions\n    exampleTestcases\n    contributors {\n      username\n      profileUrl\n      avatarUrl\n      __typename\n    }\n    topicTags {\n      name\n      slug\n      translatedName\n      __typename\n    }\n    companyTagStats\n    codeSnippets {\n      lang\n      langSlug\n      code\n      __typename\n    }\n    stats\n    hints\n    solution {\n      id\n      canSeeDetail\n      paidOnly\n      hasVideoSolution\n      paidOnlyVideo\n      __typename\n    }\n    status\n    sampleTestCase\n    metaData\n    judgerAvailable\n    judgeType\n    mysqlSchemas\n    enableRunCode\n    enableTestMode\n    enableDebugger\n    envInfo\n    libraryUrl\n    adminUrl\n    __typename\n  }\n}\n"
}

graphQLEndpoint = 'https://leetcode.com/graphql'

htmlstr = '<div>'
htmlstr += '<style> @page { size: letter landscape; margin: 2cm; }\n * { word-wrap: break-word; } pre { white-space: pre-wrap; } </style>'

questions_details = []  # To store question details
responses = []  # To store responses


def update_question_links(question_links):
  with open('question_links.txt') as f:
    links =  f.read()

  links = links.split('\n')

  for each in links:
    question_links.append(each)

def get_section(section_text):
  global htmlstr
  htmlstr += '<div>'
  htmlstr += f'<h1>{section_text[1:]}</h1>'
  htmlstr += '</div>'
  htmlstr += '<p style="page-break-before: always" ></p>'

def get_question(question_link):
    slug = question_link.split('https://leetcode.com/problems/', 1)[1]
    baseJSON['variables']['titleSlug'] = slug
    resp = requests.get(graphQLEndpoint, json=baseJSON)

    x = json.loads(resp.text, object_hook=lambda d: SimpleNamespace(**d))

    # Ensure this object is a dictionary with 'title' and 'content' keys
    question_detail = {
        'title': x.data.question.title,
        'content': x.data.question.content
    }
    questions_details.append(question_detail)

def generate_response_with_chat_api(question_title, question_content):
    new_prompt = f"""for the problem given by user, titled "{question_title}", with the content: {question_content}, give a response with:
1- Give away the key idea to solve this problem in simple, readable, one sentence
2- Give the solution in a simple, readable, detailed step by step pseudocode in natural language.
3- A well-commented python pseudocode (code comments by #)"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": new_prompt},
            {"role": "user", "content": "Please provide a solution as described."}
        ]
    )
    return response.choices[0].message.content

def generate_response_with_completion_api(question_title, question_content):
    response = openai.Completion.create(
        model="gpt-3.5-turbo",  # or "gpt-3.5-turbo", check the latest model available
        prompt=f"{question_title}: {question_content}\n\n###\n",
        temperature=0.7,
        max_tokens=150,
        top_p=1.0,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].text

def format_response(response_text):
    # Initialize formatted_response
    formatted_response = "<div>"
    
    # Attempt to split the response text for each expected section
    key_idea_split = response_text.split("1- ")
    if len(key_idea_split) > 1:
        pseudocode_split = key_idea_split[1].split("2- ")
        key_idea = pseudocode_split[0]
        formatted_response += f"<h3>Key Idea</h3><p>{key_idea}</p>"
        
        if len(pseudocode_split) > 1:
            python_code_split = pseudocode_split[1].split("3- ")
            pseudocode = python_code_split[0]
            pseudocode = simple_python_highlighter(pseudocode)
            formatted_response += f"<h3>Step-by-step Pseudocode</h3><p>{pseudocode}</p>"
            
            if len(python_code_split) > 1:
                python_code = python_code_split[1]
                python_code = simple_python_highlighter(python_code)

                # Assume python_code might have trailing "```" to remove
                python_code = python_code.replace("```", "")
                formatted_response += f"<h3>Python Pseudocode</h3><pre class='python-code'><code>{python_code}</code></pre>"
    else:
        # If the response doesn't follow the expected numbered format, just format it as a regular paragraph
        formatted_response += f"<p>{response_text}</p>"
    
    formatted_response += "</div>"
    return formatted_response


def generate_responses():
    global responses, questions_details

    for question in questions_details:
        title = question['title']
        content = question['content']
        response_text = generate_response_with_chat_api(title, content)

        # Format the response text for better readability
        formatted_response = format_response(response_text)
        
        responses.append(f"<div><h2>Response to: {title}</h2>{formatted_response}</div>")



htmlstr = '<div>'
htmlstr += '''
<style>
    @page { size: letter landscape; margin: 2cm; }
    * { word-wrap: break-word; }
    pre { white-space: pre-wrap; background-color: #f7f7f7; border: 1px solid #e1e1e8; padding: 10px; border-radius: 5px; }
    h2 { color: navy; }
    .question { margin-bottom: 20px; }
    .response { margin-top: 10px; }
    .python-code { font-family: Consolas, "Courier New", monospace; }
</style>
'''
htmlstr += '''
<style>
    /* Existing styles */
    .python-code { font-family: 'Consolas', 'Courier New', monospace; background-color: #f7f7f7; border: 1px solid #e1e1e8; padding: 10px; border-radius: 5px; }
    .keyword { color: #0077aa; font-weight: bold; }
    .string { color: #dd1144; }
    .comment { color: #999988; font-style: italic; }
</style>
'''
htmlstr += '''
<style>
    /* Previous styles */
    h3 { color: #333; }
    .python-code { background-color: #f7f7f7; border: 1px solid #e1e1e8; padding: 10px; border-radius: 5px; }
    pre, code { font-family: 'Consolas', 'Courier New', monospace; }
    /* Add styles for keyword, string, comment if doing syntax highlighting */
</style>
'''
# Continue with the existing process to format HTML and generate PDF

def simple_python_highlighter(code):
    # Python keywords for basic syntax highlighting
    keywords = [
        'def', 'return', 'for', 'while', 'if', 'else', 'elif', 'in', 
        'True', 'False', 'None', 'and', 'or', 'not', 'break', 'continue', 'class',
        'try', 'except', 'finally', 'with', 'as', 'yield', 'import', 'from', 'global',
        'nonlocal', 'assert', 'pass', 'raise'
    ]
    # Escape special characters to prevent HTML injection
    code = html.escape(code)
    
    # Highlight keywords
    # for keyword in keywords:
        # code = re.sub(r'\b' + keyword + r'\b', f"<span class='keyword'>{keyword}</span>", code)
    
    # Highlight strings
    code = re.sub(r'(\".*?\"|\'.*?\')', r"<span class='string'>\1</span>", code)
    
    # Highlight comments
    code = re.sub(r'(\#.*?(\n|$))', r"<span class='comment'>\1</span>", code)
    
    return code



# Assuming questions_details and responses are formatted as suggested
def format_html_and_generate_pdf():
    global htmlstr
    # Append formatted questions
    for question in questions_details:
        htmlstr += f"<div class='question'>{question}</div>"
    # Append formatted responses
    for response in responses:
        htmlstr += f"<div class='response'>{response}</div>"
    htmlstr += '</div>'
    HTML(string=htmlstr).write_pdf('blind_answers.pdf')

def main():
    question_links = []
    update_question_links(question_links)

    processed_questions = 0
    for line in question_links:
        if processed_questions >= 3:
            break  # Stop after processing three questions
        if line[0] == '~':
            get_section(line)
        else:
            get_question(line)  # This populates `questions_details` directly
            processed_questions += 1
    
    generate_responses()  # Corrected: No need to pass questions_details
    
    format_html_and_generate_pdf()

if __name__=='__main__':
    main()
