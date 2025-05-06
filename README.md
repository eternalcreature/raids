# raids
 
1. To run the script, you need the following
- Python (developed and tested on 3.12.4, but I imagine any version 3.9 or newer should work)
- modules listed in requirements.txt (install with "pip install -r requirements.txt")
- an internet connection

2. First step is to run the 'login.py' file to log yourself in and create cookies to store that login data in the "auth_data" folder.
   -in order to login, you will either need your login data to be stored in an '.env' file or you'll type the email and password as prompted in the terminal
   -the contents of the .env file should be as follow:
   "
KANO_EMAIL=[your_email]
KANO_PASSWORD=[your_password]
"

3. Next, paste your list of raid urls to the "links.txt" file. Each raid should be in a new line. It doesn't matter if those links were used if/when you ran the script before. Previously checked raids are stored in the database and duplicate urls are ignored

4. Once you've saved the 'links.txt' file, run the 'scan_raids.py'. It will update the database stored in the "raids_lia.csv" file.

5. Check the "updates.txt". Each line can be copy/pasted to the chat room :)

6. You can inspect the dataset in a jupyter notebook. :) The notebook in this repo sorted the dataset to show open raids with low health per open spot at the top.
 
Notes:
- it takes about one second to check each raid
- if the raid ran out of time and the boss was not killed, it will take substantially longer to check that raid. However, once the raid has been determined to fail, it won't be checked again