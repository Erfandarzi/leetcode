import requests
import json
from types import SimpleNamespace
from weasyprint import HTML
import openai
openai.api_key = "mykey"
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

# htmlstr = '<div>'
# htmlstr += '<style> @page { size: A4; margin: 2cm; } * { word-wrap: break-word; } pre { white-space: pre-wrap; } </style>'

questions_details = []  # To store question details
responses = []  # To store responses


def update_question_links(question_links):
  with open('question_links.txt') as f:
    links =  f.read()

  links = links.split('\n')

  for each in links:
    question_links.append(each)

def get_section(section_text, index):
    global htmlstr
    htmlstr += '<div>'
    htmlstr += f'<h1>{index} - {section_text[1:]}</h1>'  # Include index in header
    htmlstr += '</div>'
    htmlstr += '<p style="page-break-before: always"></p>'

def get_question(question_link, index):
    if not question_link:
        print(f"Skipping empty line at index {index}")
        return

    try:
        slug = question_link.split('https://leetcode.com/problems/', 1)[1]
        baseJSON['variables']['titleSlug'] = slug
        resp = requests.get(graphQLEndpoint, json=baseJSON)

        if resp.status_code == 200:
            response_data = json.loads(resp.text)
            if 'data' in response_data and response_data['data'] and 'question' in response_data['data']:
                question = response_data['data']['question']
                if 'title' in question and 'content' in question:
                    title = question['title']
                    content = question['content']
                else:
                    title = "No Title Available"
                    content = "No Content Available"
                    print(f"Missing 'title' or 'content' in data for {question_link}")
            else:
                title = "No Title Available"
                content = "No Content Available"
                print(f"No question data available in API response for {question_link}")
        else:
            title = "No Title Available"
            content = "No Content Available"
            print(f"HTTP Error {resp.status_code} for {question_link}")

        # Collect question details for answers
        question_detail = {
            'index': index,
            'title': title,
            'content': content
        }
        questions_details.append(question_detail)
        
    except Exception as e:
        print(f"Exception processing {question_link}: {e}")

def generate_response_with_chat_api(question_title, question_content):
    new_prompt = f"""for the problem given by user, titled "{question_title}", with the content: {question_content}, give a response with:
1- Give away the key idea to solve this problem in simple, readable, one sentence
2- Give the solution in a simple, readable, detailed step by step pseudocode in natural language.
3- A well-commented python pseudocode (code comments by #)
Be to the point and start your response in this exact template 1- The key idea to .... 2- Step by step .... 3- Python ....(no context before and after your response)"""

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
        model="gpt-4-turbo",  # or "gpt-3.5-turbo", check the latest model available
        prompt=f"{question_title}: {question_content}\n\n###\n",
        temperature=0.7,
        max_tokens=300,
        top_p=1.0,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].text

def format_response(response_text):
    # Remove <br> from pseudocode parts which will be inside <pre> tags
    response_text = response_text.replace('<br>', '\n')
    
    # Initialize formatted_response
    formatted_response = "<div>"
    
    # Split the response text for each expected section using new logic for line breaks
    sections = response_text.split("\n")
    if len(sections) > 1:
        formatted_response += f"<h3>Key Idea</h3><p>{sections[0]}</p>"
        
        pseudocode = "\n".join(sections[1:])  # Join back the rest of sections except the first
        pseudocode = simple_python_highlighter(pseudocode)
        formatted_response += f"<h3>Python Pseudocode</h3><pre class='python-code'><code>{pseudocode}</code></pre>"
    else:
        # If the response doesn't follow the expected numbered format, just format it as a regular paragraph
        formatted_response += f"<p>{response_text}</p>"
    formatted_response = "<div>" + response_text + "</div>"

    formatted_response += "</div>"
    return formatted_response
def generate_responses():
    global htmlstr
    for question in questions_details:
        index = question['index']
        title = question['title']
        content = question['content']
        response_text = generate_response_with_chat_api(title, content)  # Assuming this returns formatted text
        formatted_response = format_response(response_text)
        
        # Add index to the response heading
        htmlstr += f"<div><h2>{index} - Response to: {title}</h2>{formatted_response}</div>"


htmlstr = '''
<div>
    <style>
        @page { size: A4; margin: 2cm; }
        body { font-family: Arial, sans-serif; font-size: 10pt; } /* Smaller font size and a more readable font */
        * { word-wrap: break-word; }
        pre { 
            white-space: pre-wrap; 
            background-color: #f7f7f7; 
            border: 1px solid #e1e1e8; 
            padding: 10px; 
            border-radius: 5px; 
            font-family: 'Consolas', 'Courier New', monospace; /* Maintain the monospace font for code blocks */
            font-size: 10pt; /* Smaller font size for code blocks */
        }
        h2 { color: navy; font-size: 12pt; } /* Smaller font size for headings */
        h3 { color: #333; font-size: 11pt; } /* Smaller font size for subheadings */
        .question, .response { 
            margin-bottom: 20px; 
            margin-top: 10px; 
        }
        .python-code { 
            font-family: 'Consolas', 'Courier New', monospace; 
            background-color: #282c34; 
            color: #abb2bf; 
            border: 1px solid #e1e1e8; 
            padding: 10px; 
            border-radius: 5px; 
            font-size: 10pt; /* Smaller font size for code snippets */
        }
        .keyword { color: #0077aa; font-weight: bold; } /* Blue for keywords */
        .string { color: #dd1144; } /* Red for strings */
        .comment { color: #999988; font-style: italic; } /* Grey for comments */
        .builtin { color: #56b6c2; } /* Cyan for built-in functions */
        .decorator { color: #d19a66; } /* Light orange for decorators */
        .number { color: #d19a66; } /* Orange for numbers */
    </style>
</div>
'''



def format_response(response_text):
    formatted_response = "<div>"

    # First, replace all '<br>' with '\n' to normalize newlines
    response_text = response_text.replace('<br>', '\n')

    # Split the content by numbers followed by a dash which often denotes steps or parts
    parts = re.split(r'\n\d+-', response_text)
    print (parts)
    # Optional: check if parts exist and handle them
    if len(parts) > 1:
        # Handle Key Idea if it's generally the first unnumbered part
        formatted_response += f"<h3>Key Idea</h3><p>{parts[0].strip()}</p>"

        # Re-attach the numbers to the parts after splitting, assuming they represent steps
        for index, part in enumerate(parts[1:], start=1):
            if "python" in part.lower() or "pseudocode" in part.lower():
                # This part contains pseudocode or Python code, apply syntax highlighting
                part = simple_python_highlighter(part.strip())
                section_heading = "Python Pseudocode" if "python" in part.lower() else "General Pseudocode"
                formatted_response += f"<h3>{section_heading}</h3><pre class='python-code'><code>{part}</code></pre>"
            else:
                # General text handling
                formatted_response += f"<p>{part.strip()}</p>"
    else:
        # If no numbered parts, handle as a single block of text
        formatted_response += f"<p>{response_text.strip()}</p>"

    formatted_response += "</div>"
    return formatted_response



def simple_python_highlighter(code):
    # First, unescape any pre-escaped HTML entities that shouldn't be escaped in code blocks
    code = html.unescape(code)

    # Define regex patterns for Python syntax highlighting
    patterns = {
        'keyword': r'\b(?:def|return|for|while|if|else|elif|in|True|False|None|and|or|not|break|continue|class|try|except|finally|with|as|yield|import|from|global|nonlocal|assert|pass|raise|await|async)\b',
        'builtin': r'\b(?:range|len|print|str|int|float|list|dict|set|tuple|type)\b',
        'decorator': r'(@\w+)',
        'string': r'(\".*?\"|\'.*?\')',
        'comment': r'(\#.*)',
        'number': r'\b\d+\b'
    }

    # Function to apply HTML span tags for syntax styling
    def replace_with_style(match):
        css_class = {
            'string': "string",
            'comment': "comment",
            'number': "number",
            'builtin': "builtin",
            'decorator': "decorator"
        }.get(match.lastgroup, "keyword")
        return f'<span class="{css_class}">{html.escape(match.group())}</span>'

    # Compile regex with named groups for each syntax type
    regex = re.compile('|'.join(f'(?P<{k}>{v})' for k, v in patterns.items()))

    # Apply the syntax highlighting
    highlighted_code = regex.sub(replace_with_style, code)
    return highlighted_code

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
    index = 1  # Initialize counter for all entries
    processed_questions = 0  # Counter for questions processed

    if not question_links:
        print("No questions found in the file.")
        return

    for line in question_links:
        if not line.strip():  # Skip empty lines
            continue

        if line[0] == '~':
            get_section(line, index)
        else:
            if processed_questions >= 3:
                pass  # Stop after processing three questions
            get_question(line, index)
            processed_questions += 1
        index += 1

    generate_responses()
    format_html_and_generate_pdf()

if __name__ == '__main__':
    print('\n')
    main()

