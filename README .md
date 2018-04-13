# About

This is a website that provides a list of video games within a variety of
genres, and has user registration and authentication system through Google.
Logged in users can post, edit and delete their own video games.

# You Need:

Python 3
Vagrant
VirtualBox
Google Account

# Setup

1. Install Vagrant And VirtualBox
2. Navigate inside Udacity Category Site folder with command prompt and use 'vagrant up'
   to install vagrant machine.
3. DON'T RUN fill_database.py or database_setup.py unless using a different vagrant machine.

# To Run

1. Navigate to Udacity Category Project Folder through command prompt
2. Launch Vagrant VM by running 'vagrant up', and then 'vagrant ssh'
3. Use 'cd /vagrant' to enter and see files
4. While in the vagrant environment navigate inside Items_Catalog_Project with 'cd Items_Catalog_Project'
5. Then run view.py with 'python view.py' to launch server
6. In a browser go to http://localhost:8000/ to view site

# Accessing JSON Endpoint

The JSON endpoint returns all games in database for certain genre.

To access JSON Endpoint use the following format (Use all lower case and normal spacing):

http://localhost:8000/GENRE_HERE/json

Endpoint Returns following:
    Title
    Genre
    Wiki-Link
    Trailer Link
    HTML Summary

# Included Tables

Name: User
Cols: username - stores email associated with Google Account

      id -  Stores random int ID

Name: Games
Cols: id - Stores random int ID

      title - Title of Video Game

      genre - Genre of Video Game

      more_info - Stores Wikilink of Game

      trailers - Stores part of Youtube Link like this '/watch?v=SDSZCaOjECM'

      summary - Contains HTML summary

      user_id[ForeignKey with User.id] - If user created, contains creators ID from
                                        user table.
