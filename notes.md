python -m venv myenv

myenv\Scripts\activate
source myenv\bin\activate

conda create --name myenv python

deactivate

pip list

pip install -r requirements.txt

pip install flask
pip install django

mkdir myflaskapp
cd myflaskapp

django-admin startproject myproject .
python manage.py startapp myapp

pip freeze > requirements.txt

pip install --upgrade pip

pip freeze --local|grep-v'^\-e'|cut-d=-f1|xargs-n1 pip install --upgrade

pip install pip-review
pip-review --auto

pip install pip-tools
pip-compile --upgrade requirements.txt
pip-sync



## ngrok 
    - tunnel local ports to public URLs and inspect traffic
    - ngrok exposes local networked services behinds NATs and firewalls to the
    public internet over a secure tunnel. 
    - Share local websites, build/test webhook consumers and self-host personal services.
    - http://localhost:4040 for ngrok's web interface to inspect traffic.
## Commands Examples:
    ngrok help <command>
    ngrok http 80                    # secure public URL for port 80 web server
    ngrok http -subdomain=baz 8080   # port 8080 available at baz.ngrok.io
    ngrok http foo.dev:80            # tunnel to host:port instead of localhost
    ngrok http https://localhost     # expose a local https server
    ngrok tcp 22                     # tunnel arbitrary TCP traffic to port 22
    ngrok tls -hostname=foo.com 443  # TLS traffic for foo.com to port 443
    ngrok start foo bar baz          # start tunnels from the configuration file
## Other COMMANDS:
   authtoken    save authtoken to configuration file
   credits      prints author and licensing information
   http         start an HTTP tunnel
   start        start tunnels by name from the configuration file
   tcp          start a TCP tunnel
   tls          start a TLS tunnel
   update       update ngrok to the latest version
   version      print the version string
   help         Shows a list of commands or help for one command

# Installing Ngrok
1. Download the ngrok zip file from the official ngrok website: https://ngrok.com/download
2. Extract the zip file to a directory on your computer (e.g., C:\ngrok)
3. Add the ngrok directory to your system's PATH environment variable

# Basic Ngrok Commands
1. Start ngrok: ngrok http <port> (e.g., ngrok http 80)
2. Specify a region: ngrok http <region> <port> (e.g., ngrok http us 80)
3. Use a custom subdomain: ngrok http <subdomain>.ngrok.io <port> (e.g., ngrok http myapp.ngrok.io 80)
4. Inspect traffic: ngrok http <port> --inspect (e.g., ngrok http 80 --inspect)
5. Stop ngrok: Press Ctrl+C in the Command Prompt

# Ngrok Options
1. --region: Specify a region (e.g., us, eu, ap)
2. --subdomain: Specify a custom subdomain
3. --inspect: Inspect traffic
4. --httpauth: Specify HTTP basic auth credentials
5. --log: Specify a log file

# Example Use Cases
1. Expose a local web server: ngrok http 80
2. Expose a local API: ngrok http 8080
3. Test webhooks: ngrok http 80 --inspect
4. Demo an application: ngrok http myapp.ngrok.io 80

# Tips and Tricks
1. Use ngrok http <port> --inspect to inspect traffic.
2. Use ngrok http <subdomain>.ngrok.io <port> to specify a custom subdomain.
3. Use ngrok http <region> <port> to specify a region.
4. Press Ctrl+C to stop ngrok.

# ----------------------------------------------------------------------------------------------------------

# Basic Git Commands
0. git status: Ensure all changes are tracked and ready for commit.
1. git init: Initializes a new Git repository in the current directory.
2. git clone [repository URL]: Clones an existing Git repository from the specified URL.
3. git add [file name]: Stages a file for the next commit.
4. git add .: Stages all changes in the current directory and subdirectories.
5. git commit -m "[commit message]": Commits the staged changes with a meaningful commit message.
6. git log: Displays a log of all commits made to the repository.
7. git branch: Lists all branches in the repository.
8. git checkout [branch name]: Switches to the specified branch.
9. git merge [branch name]: Merges the specified branch into the current branch.
10. git remote add [remote name] [repository URL]: Links the local repository to a remote repository.
11. git push: Pushes the committed changes to the remote repository.
12. git pull: Pulls the latest changes from the remote repository.

# Git Workflow
1. Create a new repository using git init.
2. Add files to the repository using git add.
3. Commit the changes using git commit.
4. Create a new branch using git branch.
5. Switch to the new branch using git checkout.. git push.

# Git GUI Clients
If you prefer a graphical user interface, you can use Git GUI clients like:

- GitHub Desktop
- Git Kraken
- TortoiseGit
- Git Tower

These clients provide a user-friendly interface for managing your Git repositories.

# Git Best Practices
1. Use meaningful commit messages.
2. Use branches to manage different versions of your code.
3. Regularly push your changes to the remote repository.
4. Use git status to check the status of your repository.
5. Use git diff to review changes before committing.

git status

git checkout -b optimisations

git add .

git commit -m "
refactor(JobsModule): Improve and enhance functionality across DTOs, models, repositories, and sevice:
- Added validate_future_date to enforce future date validation on application_deadline for better data integrity
- Integrated remove_null_fields to clean serialized outputs
- Added logging for all key actions and errors to aid in debugging and improve traceability.
- Implemented custom validation and enhanced error messages for better diagnostics and debugging
- Implemented remove_null_fields to clean serialized output by removing null fields
- Wrapped create/update operations in transactions for better data integrity.
- Added handling of status, employment_type, and experience_level using fields.Enum for type safety.
- Added pagination to get_all_jobs to limit returned job records for performance improvements.
- Refactored duplicate repository methods using mixins for better maintainability and reduced code duplication.
- Refactored skill and education repositories to support batch inserts and updates.
- Improved code readability with list comprehensions for creating related data records.
- Enhanced bulk_create method to support optional commit, improving flexibility and performance for bulk inserts.
- Added bulk_create with an optional commit parameter for better transaction control.
- Added support for pagination, date-range filtering, and full-text search for get_all_jobs.
- Code refactor for the fetch_by_id_for_xml intended for better XML compatibility and enhanced data serialization
- Introduced handle_request decorator for consistent error handling across endpoints.
"

git push origin optimisations