# BotTestFk
A framework to test chatbots by using adversarial examples

This framework is implementing the whole process of chatbots described in the research paper "".

To launch it, make sure to:
- install all the requirements present in the requirements.txt file.
- configure the database (postgre).
- set the following environment keys on your machine: DB_PASSWORD, and all the API keys (list in the file "framework/helpers/api_calls.py").
- you can fill the database with the DB dump provided in the main directory. It contains the data used to test the framework on a Calendar Application.

Then launch the Django server, and feel free to use it.
Be careful, there is absolutely NO SECURITY on this website. If the website is online, anyone can submit information in the forms, there is no security check.
