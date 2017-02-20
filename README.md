# What's this little repo?

**my-book-on-sale** is a tiny repo to check whether the books in user's "to-read" shelf (or other shelves) on Goodreads are on sale on Amazon. I wrote for myself but you can use it by setting `--user` parameter for your own use.

### How does it work?

```
python sale.py --user 18882054-osman-ba-kaya --shelf to-read
```

The script starts fetching the book names in the shelf you set with `--shelf` parameter (if you do not set `--shelf`, the program runs as `--shelf=to-read`). Then the program fetches Kindle books on sale and get the intersection of titles. Print all.

### Improvement?

I think total match between titles on Goodreads and Amazon might be problematic, it will not match if they have very slight difference, and that functionality should be replaced a little bit smart way (comparing words between each title for instance) but... not really necessary.


### Cron

I also add this to my cronjob. 

```
* 15 * * *  cd ~/playground/my-book-on-sale && ~/anaconda2/bin/python sale.py 2>&1 > out.log
```
This command runs every day at 3pm (15:00) and print the output into `out.log` file. If you don't know so much about crontab, here is a basic source: https://ole.michelsen.dk/blog/schedule-jobs-with-crontab-on-mac-osx.html.

Note that I tested this code on MacOS.
