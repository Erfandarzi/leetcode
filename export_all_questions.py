import requests
import json
from types import SimpleNamespace
from weasyprint import HTML

baseJSON = {
    "operationName": "questionData",
    "variables": {
        "titleSlug": "PLACEHOLDER"
    },
    "query": """
    query questionData($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionId
        questionFrontendId
        boundTopicId
        title
        titleSlug
        content
        translatedTitle
        translatedContent
        isPaidOnly
        difficulty
        likes
        dislikes
        isLiked
        similarQuestions
        exampleTestcases
        contributors {
          username
          profileUrl
          avatarUrl
          __typename
        }
        topicTags {
          name
          slug
          translatedName
          __typename
        }
        companyTagStats
        codeSnippets {
          lang
          langSlug
          code
          __typename
        }
        stats
        hints
        solution {
          id
          canSeeDetail
          paidOnly
          hasVideoSolution
          paidOnlyVideo
          __typename
        }
        status
        sampleTestCase
        metaData
        judgerAvailable
        judgeType
        mysqlSchemas
        enableRunCode
        enableTestMode
        enableDebugger
        envInfo
        libraryUrl
        adminUrl
        __typename
      }
    }
    """
}

graphQLEndpoint = 'https://leetcode.com/graphql'

htmlstr = '<div>'
htmlstr += '<style> @page { size: letter landscape; margin: 2cm; } * { word-wrap: break-word; } pre { white-space: pre-wrap; } </style>'

def update_question_links(question_links):
    with open('question_links.txt') as f:
        links = f.read().split('\n')
    question_links.extend(links)

def get_section(section_text, index):
    global htmlstr
    htmlstr += '<div>'
    htmlstr += f'<h1>{index}: {section_text[1:]}</h1>'
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

        global htmlstr
        htmlstr += f'<div><h2>{index}: {title}</h2>{content}</div>'
        htmlstr += '<p style="page-break-before: always"></p>'

    except Exception as e:
        print(f"Exception processing {question_link}: {e}")


def main():
    question_links = []
    update_question_links(question_links)
    index = 1  # Initialize counter for questions

    if not question_links:
        print("No questions found in the file.")
        return

    for line in question_links:
        if not line.strip():  # Skip empty lines
            print(f"Skipping empty line at position {index}")
            continue

        try:
            if line[0] == '~':
                get_section(line, index)
            else:
                get_question(line, index)
                index += 1  # Increment the counter for each question
            print(f"{index}: {line}")
            print('------------------------------')
        except Exception as e:
            print(f"Error processing {line}: {str(e)}")

    global htmlstr
    htmlstr += '</div>'

    # Try block for PDF generation
    try:
        HTML(string=htmlstr).write_pdf('blind_75.pdf')
        print("PDF generated successfully.")
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")


if __name__ == '__main__':
    print('\n')
    main()
