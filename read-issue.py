import os
import re
from python_graphql_client import GraphqlClient

# Define the path to the token file
TOKEN_FILE_PATH = os.path.expanduser("~/.ssh/akyeren.gh.pat.repo.proj")

def read_token_from_file(token_file_path):
    """Reads the GitHub token from a secure file."""
    try:
        with open(token_file_path, 'r') as token_file:
            token = token_file.read().strip()
            if not token:
                raise ValueError("Token file is empty.")
            return token
    except FileNotFoundError:
        raise FileNotFoundError(f"Token file not found at {token_file_path}.")
    except Exception as e:
        raise RuntimeError(f"Error reading token file: {e}")

def fetch_project_id(client, project_name, owner, repo_name, token):
    """Fetches the project ID for the given project name."""
    query = f"""
    query {{
      repository(owner: "{owner}", name: "{repo_name}") {{
        projectsV2(first: 100) {{
          nodes {{
            id
            title
          }}
        }}
      }}
    }}
    """
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.execute(query=query, headers=headers)
    
    if 'errors' in response:
        print(f"Error fetching project ID: {response['errors']}")
        return None
    
    projects = response['data']['repository']['projectsV2']['nodes']
    for project in projects:
        if project['title'] == project_name:
            return project['id']
    
    print(f"Project '{project_name}' not found.")
    return None

def fetch_project_items(client, project_id, token):
    """Fetches items from the GitHub project and their field values."""
    query = f"""
    query {{
      node(id: "{project_id}") {{
        ... on ProjectV2 {{
          items(first: 20) {{
            nodes {{
              id
              fieldValues(first: 10) {{
                nodes {{
                  ... on ProjectV2ItemFieldTextValue {{
                    text
                    field {{
                      ... on ProjectV2FieldCommon {{
                        name
                      }}
                    }}
                  }}
                  ... on ProjectV2ItemFieldDateValue {{
                    date
                    field {{
                      ... on ProjectV2FieldCommon {{
                        name
                      }}
                    }}
                  }}
                  ... on ProjectV2ItemFieldSingleSelectValue {{
                    name
                    field {{
                      ... on ProjectV2FieldCommon {{
                        name
                      }}
                    }}
                  }}
                  ... on ProjectV2ItemFieldNumberValue {{
                    number
                    field {{
                      ... on ProjectV2FieldCommon {{
                        name
                      }}
                    }}
                  }}
                  ... on ProjectV2ItemFieldIterationValue {{
                    duration
                    startDate
                    title
                    field {{
                      ... on ProjectV2FieldCommon {{
                        name
                      }}
                    }}
                  }}
                }}
              }}
              content {{
                ... on DraftIssue {{
                  title
                  body
                }}
                ... on Issue {{
                  title
                  url
                  assignees(first: 10) {{
                    nodes {{
                      login
                    }}
                  }}
                }}
                ... on PullRequest {{
                  title
                  assignees(first: 10) {{
                    nodes {{
                      login
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
      }}
    }}
    """
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.execute(query=query, headers=headers)
    
    if 'errors' in response:
        print(f"Error fetching items: {response['errors']}")
        return None
    return response

def extract_issue_id_from_url(url):
    """Extracts the issue ID from the URL."""
    match = re.search(r'/issues/(\d+)', url)
    return match.group(1) if match else 'N/A'

def print_issue_data(response):
    """Extracts and prints the issue titles and field values from the response."""
    items = response['data']['node']['items']['nodes']
    for item in items:
        content = item['content']
        if content:
            url = content.get('url', 'N/A')
            title = content.get('title', 'N/A')
            body = content.get('body', 'N/A')
            issue_id = extract_issue_id_from_url(url)
            assignees = [assignee['login'] for assignee in content.get('assignees', {}).get('nodes', [])]

            # Display issue or pull request details
            print(f"ID: {issue_id}")
            print(f"URL: {url}")
            print(f"Title: {title}")
            if 'body' in content:
                print(f"Body: {body}")
            print(f"Assignees: {', '.join(assignees)}")
            
            # Display field values
            field_values = item['fieldValues']['nodes']
            # print(f"Fields: {field_values}")
            for field_value in field_values:
                if len(field_value) == 0: continue
                field_name = field_value.get('field', {}).get('name', 'Unknown Field')
                if 'text' in field_value:
                    value = field_value['text']
                elif 'duration' in field_value and 'startDate' in field_value and 'title' in field_value:
                    value = f"{field_value['title']}({field_value['startDate']} - {field_value['duration']})"
                elif 'date' in field_value:
                    value = field_value['date']
                elif 'name' in field_value:
                    value = field_value['name']
                else:
                    value = 'N/A'
                print(f"   {field_name}: {value}")
            print()  # Print a newline for better readability

def main():
    """Main function that orchestrates the fetching of items from the GitHub API."""
    # Step 1: Read the GitHub token from the file
    GITHUB_TOKEN = read_token_from_file(TOKEN_FILE_PATH)
    
    # Step 2: Initialize the GraphQL client
    client = GraphqlClient(endpoint="https://api.github.com/graphql")
    
    # Define your project details
    PROJECT_NAME = "SpaceX"  # Replace with your project name
    REPO_OWNER = "akyeren"  # Replace with your repository owner
    REPO_NAME = "spacex"  # Replace with your repository name
    
    # Step 3: Fetch project ID
    project_id = fetch_project_id(client, PROJECT_NAME, REPO_OWNER, REPO_NAME, GITHUB_TOKEN)
    
    # Step 4: Fetch project items if project ID is valid
    if project_id:
        response = fetch_project_items(client, project_id, GITHUB_TOKEN)
        
        # Step 5: If the response is valid, print the issue data
        if response:
            print_issue_data(response)

if __name__ == "__main__":
    main()
