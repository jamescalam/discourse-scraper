from selenium import webdriver
import time
import json

driver = webdriver.Safari()

MAP = {
    'huggingface': 'https://discuss.huggingface.co',
    'streamlit': 'https://discuss.streamlit.io',
    'pytorch': 'https://discuss.pytorch.org',
    'tensorflow': 'https://discuss.tensorflow.org'
}

for DOC in MAP.keys():
    URL = MAP[DOC]

    driver.get(URL)

    data = []

    # get categories
    cat_elems = driver.find_elements_by_xpath(
        "//a[@class='category-title-link']"
    )
    cats = []
    for elem in cat_elems:
        cats.append({
            'title': elem.get_attribute('textContent').strip(),
            'href': elem.get_attribute('href')
        })

    ignore = [
        'official announcements',
        'random',
        'show the community!',
        'community calls',
        'site feedback',
        'jobs',
        'announcements',
        'events'
    ]
    cats = [cat for cat in cats if cat['title'].lower() not in ignore]

    for cat in cats:
        print(f"Extracting '{cat['title']}'")
        try:
            driver.get(cat['href'])
        except: break
        while True:
            try:
                # Get scroll height
                last_height = driver.execute_script("return document.body.scrollHeight")
                # Scroll down to bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                # Wait to load page
                time.sleep(0.5)

                # Calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            except: break
        try:
            # now extract all threads
            thread_elems = driver.find_elements_by_xpath(
                "//a[@class='title raw-link raw-topic-link']"
            )
            threads = []
            for elem in thread_elems:
                threads.append({
                    'title': elem.get_attribute('textContent').strip(),
                    'href': elem.get_attribute('href')
                })
        except: break
        # now navigate to each thread and extract everything
        for thread in threads:
            try:
                href = thread['href']
                thread_title = thread['title']
                cat_title = cat['title']
                driver.get(href)
                # give sec to load
                time.sleep(0.1)
                # get all comments
                comment_elems = driver.find_elements_by_xpath(
                    '//div[@class="cooked"]'
                )
                # find any accepted solutions
                answer_elem = driver.find_elements_by_xpath(
                    '//span[@class="accepted-label"]/../../../../../../div[@class="cooked"]'
                )
                # sometimes there is no replies, in that case skip
                if len(comment_elems) == 1:
                    continue
                elif len(answer_elem) == 0:
                    # this means there is no marked solution, so let's try extract the first comment
                    # (we mark in the metadata that this is not confirmed solution)
                    context = comment_elems[1].get_attribute('textContent').strip()
                    marked = 0
                else:
                    # otherwise we have a marked answer, which we extract as context text
                    context = answer_elem[0].get_attribute('textContent').strip()
                    marked = 1
                # and the question at position 0 if either scenerio
                question = comment_elems[0].get_attribute('textContent').strip()
                data.append({
                    'docs': DOC,
                    'category': cat_title,
                    'thread': thread_title,
                    'href': href,
                    'question': question,
                    'context': context,
                    'marked': marked
                })
            except Exception as e:
                print(e)
                break

            with open(f'./data/{DOC}-qa.jsonl', 'w') as fp:
                for line in data:
                    fp.write(json.dumps(line) + '\n')