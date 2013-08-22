import twitter
import datetime
import time
from scipy.stats.stats import pearsonr

stranke = ["PozitivnaSlo", "strankaSDS", "strankaSD","strankaDL","strankaSLS","NovaSlovenija"]
poslanci ={
"PozitivnaSlo":[
     "MJaniPS",
     "majusdimi",
     "RBrunskole",
     "GObrane",
     "aljosajeric",
     "barbarazgajner"
 ],
"strankaSDS":[
     "drVinkoGorenak",
     "MPogacnik",
     "RomanaTomc",
     "Andrejcus",
     "BreznikFranc",
     "RoberHrovat",
     "BrankoGrims1",
     "IvanGrill",
     "dragutinmate",
     "KDanijel",
     "SONJARAMSAK",
     "pucnik1",
     "StefanTisel"
],
"strankaSD":[
    "matevzfrangez",
    "BevkSamo",
    "ljubicajelusic"
],
"strankaDL":[
    "PoloncaKomar",
    "KatarinaHocevar",
    "jeanmark00",
],
"DeSUS":[
    "IvanHrsak",
    "JanaJanca",
],
"strankaSLS":[
    "JasminaOpec"
],
"NovaSlovenija":[
    "LjudmilaNovak",
    "jozefhorvat"
]}

# Funkcija za povezavo s Twitterjem [1]
def connect():
    # Potrebne podatke se dobi na http://twitter.com/apps/new,
    # kjer je potrebno ustvariti novo aplikacijo
    CONSUMER_KEY = ''
    CONSUMER_SECRET = ''
    OAUTH_TOKEN = ''
    OAUTH_TOKEN_SECRET = ''
    auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
    return twitter.Twitter(auth=auth)

# Funkcija za shranjevanje podatkov v mongodb [1]
def save_to_mongo(data, mongo_db, mongo_db_coll, **mongo_conn_kw):
    client = pymongo.MongoClient(**mongo_conn_kw)
    db = client[mongo_db]
    coll = db[mongo_db_coll]
    return coll.insert(data)

# Funkcija za nalagnje podatkov iz mongodb [1]
def load_from_mongo(mongo_db, mongo_db_coll, **mongo_conn_kw):
    client = pymongo.MongoClient(**mongo_conn_kw)
    db = client[mongo_db]
    coll = db[mongo_db_coll]
    return [ item for item in coll.find() ]

# Funkcija, ki izra?una podatke za tretje poglavje
def tretje_poglavje(twitter_api, stranke):
    meseci = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    danes = time.localtime()
    volitve = [28.51, 26.19, 10.52, 8.37, 6.83, 4.88] # Uspeh na volitvah
    sledilci = []
    prijatelji = []
    tweets = []
    aktivnosti = []
    for stranka in stranke:
        result = twitter_api.users.show(screen_name=stranka)
        statuses = result["statuses_count"]
        created = result["created_at"].split()
        print stranka
        print "statusi:", statuses
        print "ustvarjeno:", created[2], created[1], created[5]
        a = datetime.date(danes.tm_year,danes.tm_mon,danes.tm_mday)
        b = datetime.date(int(created[5]),meseci.index(created[1])+1,int(created[2]))
        aktivnost = 1.*statuses / (a-b).days
        print "aktivnost:", aktivnost
        print "sledilci:", response["followers_count"]
        print "prijatelji:", response["friends_count"]
        following, followers = get_friends_followers_ids(twitter_api, screen_name=stranka)
        presek = [val for val in followers if val in following]
        print "presek:", len(presek)
        sledilci.append(response["followers_count"])
        prijatelji.append(response["friends_count"])
        tweets.append(statuses)
        aktivnosti.append(aktivnost)

    print "Korelacije:"
    print "Volitve-sledilci", pearsonr(volitve,sledilci)
    print "Volitve-prijatelji", pearsonr(volitve,prijatelji)
    print "Volitve-objave", pearsonr(volitve,tweets)
    print "Volitve-aktivnost", pearsonr(volitve,aktivnost)
    print "Sledilci-prijatelji", pearsonr(sledilci,prijatelji)
    print "Sledilci-objave", pearsonr(sledilci,tweets)
    print "Sledilci-aktivnost", pearsonr(sledilci,aktivnosti)
    print "Prijatelji-objave", pearsonr(prijatelji,tweets)
    print "Prijatelji-aktivnost", pearsonr(prijatelji,aktivnosti)
    print "Objave-aktivnost", pearsonr(tweets,aktivnosti)

# Funkcije za izra?uan leksikalne raznolikosti, prirejeno po [1]
# A function for computing lexical diversity (1 -> vsaka beseda samo enkrat)
def lexical_diversity(tokens):
    return 1.0*len(set(tokens))/len(tokens)
# A function for computing the average number of words per tweet
def average_words(statuses):
    total_words = sum([ len(s.split()) for s in statuses ])
    return 1.0*total_words/len(statuses)
def texts(twitter_api, stranke):
    for stranka in stranke:
        max_counter = twitter_api.users.show(screen_name=stranka)["statuses_count"]
        if max_counter > 3200: max_counter=3200
        statuses = twitter_api.statuses.user_timeline(screen_name=stranka, count=200)
        next_id = statuses[-1]['id'] - 1
        counter = 200
        status_texts =  [status["text"] for status in statuses]
        screen_names = [user_mention['screen_name'] for status in statuses for user_mention in status['entities']['user_mentions']]
        hashtags = [hashtag['text'] for status in statuses for hashtag in status['entities']['hashtags']]
        while counter < max_counter:
            statuses = twitter_api.statuses.user_timeline(screen_name=stranka, count=200, max_id=next_id)
            counter = counter + 200
            next_id = statuses[-1]['id'] - 1
            status_texts.extend([status["text"] for status in statuses])
            screen_names.extend([user_mention['screen_name'] for status in statuses for user_mention in status['entities']['user_mentions']])
            hashtags.extend([hashtag['text'] for status in statuses for hashtag in status['entities']['hashtags']])
        words = [w for t in status_texts for w in t.split()]
        pari = []
        for text in status_texts:
            split = text.split()
            pari.extend([split[i]+" "+split[i+1] for i in range(len(split)-1) ])
        print stranka
        print lexical_diversity(words)
        print lexical_diversity(screen_names)
        print lexical_diversity(hashtags)
        print average_words(status_texts)
        save_to_mongo({"words":words},"words",stranka)
        save_to_mongo({"screen_name":screen_names},"mentions",stranka)
        save_to_mongo({"tags":hashtags},"hashtags",stranka)
        # Filtriranje besed
        for word in ["v", "in", "je", "za", "na", "da", "se", "o","bo","ob","ne","z","ki","so","k","s","tudi","bi","ni","V","iz","smo","kot","pa","bomo","po",":","...","|","-","&","2/2"]:
            words = filter(lambda a: a != word, words)
        for item in [words, screen_names, hashtags, pari]:
            c = Counter(item)
            print c.most_common()[:20] # top 20
        print "-------------------"

def cos_sim(x,y):
    #Izracuna kosinusno podobnost med dvema vektorjema
    print x,y
    if len(x) == 0 or len(y) == 0:
        return maxint
    return dot_product(x,y) / (len_vektor(x) * len_vektor(y))
def len_vektor(a):
    #Izracuna dolzino vektorja
    return math.sqrt(sum(x**2 for x in a.values()))
def dot_product(x,y):
    #Izracuna produkt dveh vektorjev
    return sum(v1*y.get(k1,0) for k1,v1 in x.items())
# Primer klica: dendrogram(stranke,"hashtags","tags")
def dendrogram(stranke,db,name):
    vektorji = [[Counter(load_from_mongo(db,stranka)[-1][name])] for stranka in stranke]
    stranke = [[stranka] for stranka in stranke]
    for i in range(len(stranke)-1):
        podobnost, str1, str2, x = 0, "", "", zip(stranke, vektorji)
        for stranka1 in x[:len(stranke)-1]:
            for stranka2 in x[x.index(stranka1)+1:]:
                tmp = sum(sum(cos_sim(value1,value2) for value2 in stranka2[1])for value1 in stranka1[1])/(len(stranka2[1]) * len(stranka1[1]))
                if tmp > podobnost:
                    podobnost, str1, str2 = tmp, stranka1[0], stranka2[0]
        print str1, str2, 1-podobnost
        a,b = str1, vektorji[stranke.index(str1)]
        a.extend(str2)
        b.extend(vektorji[stranke.index(str2)])
        stranke.append(a)
        vektorji.append(b)
        vektorji.pop(stranke.index(str2))
        vektorji.pop(stranke.index(str1))
        stranke.pop(stranke.index(str1))
        stranke.pop(stranke.index(str2))

# Funkcija za klicanje Twitter API-ja, ki skrbi za razne napake [1]
def make_twitter_request(twitter_api_func, max_errors=30000, *args, **kw):
    # A nested helper function that handles common HTTPErrors. Return an updated value
    # for wait_period if the problem is a 503 error. Block until the rate limit is reset if
    # a rate limiting issue
    def handle_twitter_http_error(e, wait_period=2, sleep_when_rate_limited=True):

        if wait_period > 3600: # Seconds
            print >> sys.stderr, 'Too many retries. Quitting.'
            raise e

        # See https://dev.twitter.com/docs/error-codes-responses for common codes

        if e.e.code == 401:
            print >> sys.stderr, 'Encountered 401 Error (Not Authorized)'
            return None
        elif e.e.code == 429:
            print >> sys.stderr, 'Encountered 429 Error (Rate Limit Exceeded)'
            if sleep_when_rate_limited:
                print >> sys.stderr, "Sleeping for 15 minutes, and then I'll try again...ZzZ..."
                sys.stderr.flush()
                time.sleep(60*15 + 5)
                print >> sys.stderr, '...ZzZ...Awake now and trying again.'
                return 2
            else:
                raise e # Allow user to handle the rate limiting issue however they'd like
        elif e.e.code in (502, 503):
            print >> sys.stderr, 'Encountered %i Error. Will retry in %i seconds' % (e.e.code,
                    wait_period)
            time.sleep(wait_period)
            wait_period *= 1.5
            return wait_period
        elif e.e.code in (404,500):
            print >> sys.stderr, 'Encountered 404 or 500 Error (page does not exist)'
            return None
        else:
            raise e
    # End of nested helper function
    wait_period = 2
    error_count = 0
    while True:
        try:
            return twitter_api_func(*args, **kw)
        except twitter.api.TwitterHTTPError, e:
            error_count = 0
            wait_period = handle_twitter_http_error(e, wait_period)
            if wait_period is None:
                return
        except URLError, e:
            error_count += 1
            print >> sys.stderr, "URLError encountered. Continuing."
            if error_count > max_errors:
                print >> sys.stderr, "Too many consecutive errors...bailing out."
                raise
# Pridobi vse prijatelje in sledilce za dano uporabnisko ime ali id [1]
def get_friends_followers_ids(twitter_api, screen_name=None, user_id=None,
                              friends_limit=maxint, followers_limit=maxint):

    # Must have either screen_name or user_id (logical xor)
    assert (screen_name != None) != (user_id != None), "Must have screen_name or user_id, but not both"

    # See https://dev.twitter.com/docs/api/1.1/get/friends/ids  and
    # See https://dev.twitter.com/docs/api/1.1/get/followers/ids for details on API parameters

    get_friends_ids = partial(make_twitter_request, twitter_api.friends.ids, count=5000)
    get_followers_ids = partial(make_twitter_request, twitter_api.followers.ids, count=5000)

    friends_ids, followers_ids = [], []

    #print [len(friends_ids),len(followers_ids)]
    #if len(friends_ids)+len(followers_ids)==0: return [],[]

    for twitter_api_func, limit, ids, label in [
                                 [get_friends_ids, friends_limit, friends_ids, "friends"],
                                 [get_followers_ids, followers_limit, followers_ids, "followers"]
                             ]:
        if friends_limit == -1:
            friends_limit = 0
            continue


        cursor = -1
        while cursor != 0:
            #print user_id

            # Use make_twitter_request via the partially bound callable...
            if screen_name:
                response = twitter_api_func(screen_name=screen_name, cursor=cursor)
            else: # user_id
                response = twitter_api_func(user_id=user_id, cursor=cursor)
            #print [ids, response]
            if response==None: return [],[]
            ids += response['ids']
            cursor = response['next_cursor']

            print >> sys.stderr, 'Fetched {0} total {1} ids for {2}'.format(len(ids), label, (user_id or screen_name))

            # Consider storing the ids to disk during each iteration to provide an
            # an additional layer of protection from exceptional circumstances

            if len(ids) >= limit:
                break

    # Do something useful with the ids like store them to disk...
    return friends_ids[:friends_limit], followers_ids[:followers_limit]


# Za seznam uporabniskih imen shrani id-je prijateljev in sledilcev v mongodb
def shrani_vse_prijatelje_sledilce(t,stranke):
    for stranka in stranke:
        id_stranke = t.users.show(screen_name=stranka)["id"]
        friends, followers = get_friends_followers_ids(t, user_id=id_stranke, friends_limit=-1)
        save_to_mongo({"ids": followers}, "sledilci", stranka)
        save_to_mongo({"ids": friends}, "prijatelji", stranka)

# Pridobi id iz seznama uporabniskih imen in jih shrani v mongodb
def shrani_id_strank(t,stranke):
    id_strank = []
    for stranka in stranke:
        id_stranke = t.users.show(screen_name=stranka)["id"]
        id_strank.append(id_stranke)
    save_to_mongo({"ids" : id_strank}, "diploma", "id_strank")


#----------------------------------------
# [1] https://github.com/ptwobrussell/Mining-the-Social-Web-2nd-Edition
#
#
#
#
#