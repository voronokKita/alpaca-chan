### 2022.AUG.2

I began to fixate the development process. <br>
Last commit _a3f46ccac92ae354cb6f846f848ef0ce78a7ab0a_

1st half of the day: <br>
Wrote all the tests to the accounts app.

2nd half of the day: <br>
The application database name in presets.py. <br>
Test that some base resources of each app exist. <br>
Test the core app and some integrity tests.

### 2022.AUG.3

1st half of the day: <br>
I wrote all the tests for the navbar of all the apps. <br>
This is where I finished writing the tests, for now. But I will still read the django documentation on testing, maybe I will get some new ideas.

2nd half of the day: <br>
Some small tests optimization. Special reduced logger configuration for tests. <br>

### 2022.AUG.4

Reading documentation and writing models for the auctions app.

### 2022.AUG.5

1st half of the day: <br>
Found and fixed an unpleasant hidden bug in the accounts app - redirect after success. <br>
Stuck on trying to link an auctions app user profile to a user entry in django.

2nd half of the day: <br>
Optimized database routes. <br>
I learned that django doesn't support relationships between multiple databases. <br>
Implemented the creation of auctions profiles through signals, after a new user created. <br>
Few model tests.

### 2022.AUG.7

Wrote a few model tests and the auctions models extensions.

### 2022.AUG.8

1st half of the day: <br>
Finished auctions' models tests. Added unique_slugify util.

2nd half of the day: <br>
Made a Log model for auctions, integrated its logic and wrote all the tests.

### 2022.AUG.9 :: Auctions

###### 1st half of the day
Image upload & deletion logic and adapted the tests for it. <br>
Profile cascade deletion (and tests). Pre_delete signal.
###### 2nd half of the day
Money and bets logic. User logs function. Base_urls. Signal logger on some models. <br>
Base views, urls and templates. <br>
All the tests.

### 2022.AUG.10

###### Project
Some misc with logs and navbar header.

###### Auctions
Profile now can change its username after it's User model. <br>
Admin models. <br>
Bid values aggregation and some other misc.
