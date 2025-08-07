import json

def handler(event, context):
    """
    A simple test function that returns a success message.
    Helps diagnose if the Netlify Functions environment is working correctly.
    """
    print("--- Test function executed successfully! ---")
    return {
        'statusCode': 200,
        'headers': { 'Content-Type': 'application/json' },
        'body': json.dumps({ 'message': 'Hello from the test function! It works!' })
    }
```toml
# netlify.toml

# This configuration is for a web app with a backend function.
# The schedules from the previous version are no longer needed.

[build]
  # This tells Netlify where to find your site's files.
  # Since index.html is in the root, we can set it to the root.
  publish = "." 

[functions]
  # This tells Netlify where to find your function files.
  directory = "netlify/functions/"
