import json
from bs4 import BeautifulSoup

Name = "name"
Headline = "headline"
Locations = "locations"
Employments = "employments"
Educations = "educations"
Description = "description"



class DataPraser:

    @staticmethod
    def parse_user_followees(data):
        followees = list()
        for user in data:
            followee = {}
            followee['token'] = user['url_token']
            followee['name'] = user['name']
            # if user['is_followed'] is False:
            #     one_way_followed.append(followee)
            # else:
            followees.append(followee)
            del followee

        return followees

    @staticmethod
    def parse_user_followers(data):
        followers = list()
        for user in data:
            follower = {}
            follower['token'] = user['url_token']
            follower['name'] = user['name']
            # if usrr['is_followed'] is False:
            #     ore_way_followed.append(followee)
            # else:r
            followers.append(follower)
            # print(follower)
        return followers

    @staticmethod
    def parse_user_info(content, token):
        if content is None:
            print('Returning')
            return dict()
        obj = BeautifulSoup(content, "html.parser")
        # 寻找名字和headline
        simple = obj.find('div', {"id": "root"})
        sim = simple.find('div')
        s = sim.find('div', {'class': 'Profile-name'})
        name = s.text
        s = sim.find('div', {"class": 'RichText ztext Profile-headline'})
        headline = s.text
        del obj
        obj = BeautifulSoup(content, 'html.parser')
        # 寻找居住地，教育经历，职业生涯，个人描述
        # tag = obj.find('div',{'id':'data'})  　是following的时候直接这个？
        # 向https://www.zhihu.com/people/tiancaixinxin/following 请求会 被重定向成 acticities
        # 两者的content对user_info 的解析不同
        data = obj.find('script',{"id":"js-initialData"})
        data_state_json = json.loads(data.text)['initialState']
        # print(data_state_json)
        entities = data_state_json['entities']
        # print(entities)
        # 取出entities，是信息集合体 keys = ['users', 'questions', 'answers', 'articles', 'columns', 'topics', 'roundtables', 'favlists', 'comments', 'notifications', 'ebooks', 'activities', 'feeds', 'pins', 'promotions', 'drafts']
        # users 是个人信息集合体，keys = ['doctor-40-62'],user是个人信息
        user = entities['users'][token]
        # user   keys = ['avatarUrlTemplate', 'uid', 'avatarUrl', 'followNotificationsCount', 'isActive', 'userType', 'editorInfo', 'isBindPhone',
        #  'accountStatus', 'defaultNotificationsCount', 'isForceRenamed', 'urlToken', 'id', 'messagesCount', 'name', 'headline', 'badge',
        # 'isAdvertiser', 'renamedFullname', 'isOrg', 'gender', 'url', 'type', 'voteThankNotificationsCount', 'isFollowed', 'educations',
        # 'followingCount', 'voteFromCount', 'includedText', 'pinsCount', 'isFollowing', 'isPrivacyProtected', 'includedArticlesCount', 'favoriteCount',
        # 'voteupCount', 'commercialQuestionCount', 'isBlocking', 'followingColumnsCount', 'participatedLiveCount', 'followingFavlistsCount',
        # 'favoritedCount', 'followerCount', 'employments', 'avatarHue', 'followingTopicCount', 'description', 'business', 'columnsCount',
        # 'thankToCount', 'mutualFolloweesCount', 'coverUrl', 'thankFromCount', 'voteToCount', 'isBlocked', 'answerCount', 'allowMessage',
        # 'articlesCount', 'questionCount', 'locations', 'includedAnswersCount', 'messageThreadToken', 'logsCount', 'followingQuestionCount',
        # 'thankedCount', 'hostedLiveCount']

        educations = user[Educations]
        employments = user[Employments]
        locations = user[Locations]
        description = user[Description]
        # print(educations)
        # print(employments)
        # print(locations)

        user_info = {
                     Name: name,
                     Headline: headline,
                     Locations: DataPraser.parseLocations(locations),
                     Educations: DataPraser.parseEducations(educations),
                     Employments: DataPraser.parseEmployments(employments),
                     Description: DataPraser.clean_description(description)
                     # token , mutual, one_way
                     }
        return user_info

    @staticmethod
    def parseEducations(edu):
        edu_data = []
        for i in edu:
            data = dict()
            if 'school' in i:
                school = i['school']
                data.update({"school_name": school['name']})
            if 'major' in i:
                major = i['major']
                data.update({'major_name': major['name']})
            if len(data) != 0:
                edu_data.append(data)
        return edu_data

    @staticmethod
    def parseEmployments(emp):
        emp_data = []
        for i in emp:
            data = {}
            if 'company' in i:
                company_data = i['company']
                company_name = company_data['name']
                data.update({'company_name': company_name})
                emp_data.append(data)
        return emp_data

    @staticmethod
    def parseLocations(loc):
        loc_data = []
        for i in loc:
            data = {}
            if 'name' in i.keys():
                city_name = i['name']
                data.update({"city_name": city_name})
                loc_data.append(data)
        return loc_data

    @staticmethod
    def clean_description(des):
        des = des.replace('<br>', '\n')
        return des