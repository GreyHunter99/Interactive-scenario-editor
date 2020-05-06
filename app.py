from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = 'extra secret key'


def createList(catalog):
    "Funkcja tworząca listę użytkowników lub scenariuszy"
    itemList = {}
    folder = os.listdir(PROJECT_ROOT + "/database/" + catalog + "/")
    folder.sort(key=lambda x: int(x.split(".")[0]))
    for file in folder:
        with open(PROJECT_ROOT + "/database/" + catalog + "/" + file, "r") as read_file:
            currentFile = json.load(read_file)
        itemList.update(currentFile)
    return itemList


scenarioList = createList('scenarios')
userList = createList('users')


@app.route('/')
def menu():
    global userList

    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))

    if session.get('userId') and userList[session['userId']]['isAdmin']:
        isAdmin = True
    else:
        isAdmin = False

    return render_template('menu.html', isAdmin=isAdmin)


@app.route('/gamebooks')
def gamebooks():
    return render_template('gamebooks.html')


@app.route('/instructions')
def instructions():
    return render_template('instructions.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    global userList
    if session.get('userId'):
        return redirect(url_for('menu'))

    if request.method == 'POST' and request.form.get('username') and request.form.get('password'):
        for user in userList:
            if userList[user]['username'] == request.form['username']:
                if userList[user]['password'] == request.form['password']:
                    session['userId'] = user
                    session.pop('scenarioId', None)
                    session.pop('questionId', None)
                    session.pop('scenarioPath', None)
                    return redirect(url_for('menu'))
                return render_template('login.html', wrongPassword=True)
        return render_template('login.html', wrongUsername=True)

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    global userList
    if session.get('userId'):
        return redirect(url_for('menu'))

    if request.method == 'POST' and request.form.get('username') and request.form.get('password') and request.form.get('repeatPassword'):
        for user in userList:
            if userList[user]['username'] == request.form['username']:
                return render_template('register.html', usernameTaken=True)
        if request.form['password'] != request.form['repeatPassword']:
            return render_template('register.html', wrongPasswords=True)
        if userList == {}:
            key = '0'
        else:
            key = str(int(max(userList, key=int)) + 1)
        userList[key] = {'id': key, 'username': request.form['username'], 'password': request.form['password'], 'description': '', 'isAdmin': False}
        saveToDatabase(key + '.json', {key: userList[key]}, 'users')
        session['userId'] = key
        session.pop('scenarioId', None)
        session.pop('questionId', None)
        session.pop('scenarioPath', None)
        return redirect(url_for('menu'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('menu'))


@app.route('/changePassword', methods=['GET', 'POST'])
def changePassword():
    global userList

    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))

    userId = request.args.get('userId')

    if not userId or not session.get('userId') or (userId != session['userId'] and not userList[session['userId']]['isAdmin']):
        return redirect(url_for('menu'))

    if userList[session['userId']]['isAdmin'] and userId != session['userId']:
        noOldPassword = True
    else:
        noOldPassword = False

    if request.method == 'POST' and request.form.get('newPassword') and request.form.get('repeatNewPassword') and (noOldPassword or request.form.get('oldPassword')):
        if noOldPassword or request.form['oldPassword'] == userList[userId]['password']:
            if request.form['newPassword'] == request.form['repeatNewPassword']:
                userList[userId]['password'] = request.form['newPassword']
                saveToDatabase(userId + '.json', {userId: userList[userId]}, 'users')
                return redirect(url_for('userProfile', userId=userId))
            else:
                return render_template('changePassword.html', noOldPassword=noOldPassword, userId=userId, wrongNewPasswords=True)
        else:
            return render_template('changePassword.html', noOldPassword=noOldPassword, userId=userId, wrongOldPassword=True)

    return render_template('changePassword.html', noOldPassword=noOldPassword, userId=userId)


@app.route('/grantAdmin')
def grantAdmin():
    global userList

    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))

    userId = request.args.get('userId')

    if not userId or not session.get('userId') or not userList[session['userId']]['isAdmin'] or userId == session.get('userId'):
        return redirect(url_for('menu'))

    if not userList[userId]['isAdmin']:
        userList[userId]['isAdmin'] = True
    else:
        userList[userId]['isAdmin'] = False
    saveToDatabase(userId + '.json', {userId: userList[userId]}, 'users')

    return redirect(url_for('userProfile', userId=userId))


@app.route('/users')
def users():
    global userList

    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))

    if not session.get('userId') or not userList[session['userId']]['isAdmin']:
        return redirect(url_for('menu'))

    return render_template('users.html', userList=userList)


@app.route('/deleteUser', methods=['GET', 'POST'])
def deleteUser():
    global scenarioList, userList

    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))

    userId = request.args.get('userId')

    if not session.get('userId') or not userId or userId not in userList or (userId != session['userId'] and not userList[session['userId']]['isAdmin']):
        return redirect(url_for('menu'))

    if request.args.get('confirmDelete') and request.method == 'POST' and request.form.get('deleteUserScenarios'):
        isAdmin = userList[session['userId']]['isAdmin']
        for scenarioId in list(scenarioList):
            if scenarioList[scenarioId]['user'] == userId:
                if request.form['deleteUserScenarios'] == 'Tak':
                    del scenarioList[scenarioId]
                    os.remove(PROJECT_ROOT + "/database/scenarios/" + scenarioId + ".json")
                else:
                    scenarioList[scenarioId]['user'] = ''
                    saveToDatabase(scenarioId + '.json', {scenarioId: scenarioList[scenarioId]}, 'scenarios')
        del userList[userId]
        os.remove(PROJECT_ROOT + "/database/users/" + userId + ".json")
        if isAdmin:
            return redirect(url_for('menu'))
        else:
            return redirect(url_for('logout'))

    elementName = 'user'
    elementId = userId
    userName = userList[userId]['username']

    return render_template('delete.html', userName=userName, elementName=elementName, elementId=elementId)


@app.route('/userProfile', methods=['GET', 'POST'])
def userProfile():
    global scenarioList, userList

    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))

    userId = request.args.get('userId')

    if userId and userId in userList:
        pass
    elif session.get('userId'):
        userId = session['userId']
    else:
        return redirect(url_for('menu'))

    if session.get('userId') and userList[session['userId']]['isAdmin']:
        isAdmin = True
    else:
        isAdmin = False

    if session.get('userId') and userId == session['userId']:
        isGranted = True
    else:
        isGranted = False

    userData = dict(userList[userId])
    del userData['password']

    userScenarioList = {'privateScenarios': {}, 'publicScenarios': {}, 'publicEditScenarios': {}}
    for key, scenario in scenarioList.items():
        if scenario['user'] == userId:
            if not scenario['publicView']:
                userScenarioList['privateScenarios'][key] = scenario['name']
            elif scenario['publicEdit']:
                userScenarioList['publicEditScenarios'][key] = scenario['name']
            else:
                userScenarioList['publicScenarios'][key] = scenario['name']

    if request.method == 'POST' and request.form.get('username') and request.form.get('description') is not None and (isGranted or isAdmin):
        for user in userList:
            if userList[user]['username'] == request.form['username'] and user != userId:
                return render_template('userProfile.html', isAdmin=isAdmin, isGranted=isGranted, userScenarioList=userScenarioList, userData=userData, usernameTaken=True)
        userList[userId]['username'] = request.form['username']
        userList[userId]['description'] = request.form['description']
        saveToDatabase(userId + '.json', {userId: userList[userId]}, 'users')

    return render_template('userProfile.html', isAdmin=isAdmin, isGranted=isGranted, userScenarioList=userScenarioList, userData=userData)


@app.route('/deleteScenario')
def deleteScenario():
    global scenarioList, userList

    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))

    scenarioId = request.args.get('scenarioId')

    if not session.get('userId') or not scenarioId or scenarioId not in scenarioList or (scenarioList[scenarioId]['user'] != session['userId'] and not userList[session['userId']]['isAdmin']):
        return redirect(url_for('menu'))

    scenario = scenarioList[scenarioId]

    if request.args.get('confirmDelete'):
        userId = scenario['user']
        del scenario
        os.remove(PROJECT_ROOT + "/database/scenarios/" + scenarioId + ".json")
        return redirect(url_for('userProfile', userId=userId))

    elementName = 'scenario'
    elementId = scenarioId
    scenarioName = scenario['name']
    scenarioOwner = scenario['user']

    return render_template('delete.html', scenarioName=scenarioName, scenarioOwner=scenarioOwner, elementName=elementName, elementId=elementId)


@app.route('/scenarios')
def scenarios():
    global scenarioList

    publicScenarioList = {'publicScenarios': {}, 'publicEditScenarios': {}}
    for key, scenario in scenarioList.items():
        if scenario['publicView']:
            if scenario['publicEdit']:
                publicScenarioList['publicEditScenarios'][key] = scenario['name']
            else:
                publicScenarioList['publicScenarios'][key] = scenario['name']

    return render_template('scenarios.html', publicScenarioList=publicScenarioList)


@app.route('/start', methods=['GET', 'POST'])
def start():
    global scenarioList, userList

    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))

    scenarioId = request.args.get('scenarioId')

    if scenarioId:
        if scenarioId in scenarioList:
            scenario = scenarioList[scenarioId]
            if scenario['publicView'] or (session.get('userId') and (scenario['user'] == session['userId'] or userList[session['userId']]['isAdmin'])):
                session['scenarioId'] = scenarioId
                session.pop('questionId', None)
        else:
            return redirect(url_for('menu'))
    elif session.get('scenarioId') and session['scenarioId'] in scenarioList:
        scenario = scenarioList[session['scenarioId']]
        if not scenario['publicView'] and (not session.get('userId') or (scenario['user'] != session['userId'] and not userList[session['userId']]['isAdmin'])):
            return redirect(url_for('scenarios'))
    else:
        return redirect(url_for('scenarios'))

    session['scenarioPath'] = []

    if session.get('userId') and ((scenario['publicView'] and scenario['publicEdit']) or scenario['user'] == session['userId'] or userList[session['userId']]['isAdmin']):
        isGranted = True
    else:
        isGranted = False

    if scenario['user'] in userList:
        ownerExists = True
    else:
        ownerExists = False

    if request.method == 'POST' and request.form.get('startingAnswer'):
        for questionId in scenario['questions']:
            for keyWord in scenario['questions'][questionId]['keyWords'].values():
                if keyWord.lower() in request.form['startingAnswer'].lower():
                    scenarioPath = session['scenarioPath']
                    scenarioPath.append({'question': questionId, 'answer': "", 'startingAnswer': request.form.get('startingAnswer')})
                    session['scenarioPath'] = scenarioPath
                    return redirect(url_for('question'))
        return render_template('start.html', scenario=scenario, isGranted=isGranted, ownerExists=ownerExists, noKeyWords=True)

    return render_template('start.html', scenario=scenario, isGranted=isGranted, ownerExists=ownerExists)


@app.route('/question')
def question():
    global scenarioList, userList

    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))

    if session.get('scenarioId') and session['scenarioId'] in scenarioList:
        scenario = scenarioList[session['scenarioId']]
        if not scenario['publicView'] and (not session.get('userId') or (scenario['user'] != session['userId'] and not userList[session['userId']]['isAdmin'])):
            return redirect(url_for('start'))
    else:
        return redirect(url_for('start'))

    questionId = request.args.get('questionId')
    answerId = request.args.get('answerId')

    if questionId and questionId in scenario['questions'] and answerId and session['scenarioPath']:
        answers = scenario['questions'][session['scenarioPath'][-1]['question']]['answers']
        if answerId in answers:
            answer = answers[answerId]
            if answer['questionId'] == questionId:
                condition = True
                noExclusion = True
                if answer['conditionalAnswerId']:
                    condition = False
                if answer['exclusionAnswerId']:
                    noExclusion = False
                if not condition or not noExclusion:
                    noExclusion = True
                    for record in session['scenarioPath']:
                        if answer['exclusionAnswerId'] == record['question']+"-"+record['answer']:
                            noExclusion = False
                            break
                        if not condition and answer['conditionalAnswerId'] == record['question']+"-"+record['answer']:
                            condition = True
                if condition and noExclusion:
                    scenarioPath = session['scenarioPath']
                    scenarioPath.append({'question': questionId, 'answer': ""})
                    scenarioPath[-2]['answer'] = answerId
                    session['scenarioPath'] = scenarioPath
        return redirect(url_for('question'))

    if request.args.get('goBack') and scenario['goBack'] and session['scenarioPath']:
        scenarioPath = session['scenarioPath']
        scenarioPath.pop()
        session['scenarioPath'] = scenarioPath

    if session['scenarioPath'] and session['scenarioPath'][-1]['question'] in scenario['questions']:
         currentQuestion = session['scenarioPath'][-1]['question']
    else:
        return redirect(url_for('start'))

    if session.get('userId') and ((scenario['publicView'] and scenario['publicEdit']) or scenario['user'] == session['userId'] or userList[session['userId']]['isAdmin']):
        isGranted = True
    else:
        isGranted = False

    answers = dict(scenario['questions'][session['scenarioPath'][-1]['question']]['answers'])
    for answerId in list(answers):
        condition = True
        noExclusion = True
        if answers[answerId]['conditionalAnswerId']:
            condition = False
        if answers[answerId]['exclusionAnswerId']:
            noExclusion = False
        if not condition or not noExclusion:
            noExclusion = True
            for record in session['scenarioPath']:
                if record['answer'] and answers[answerId]['exclusionAnswerId'] == record['question']+"-"+record['answer']:
                    noExclusion = False
                    break
                if record['answer'] and not condition and answers[answerId]['conditionalAnswerId'] == record['question']+"-"+record['answer']:
                    condition = True
        if not condition or not noExclusion:
            del answers[answerId]

    optionalTexts = dict(scenario['questions'][session['scenarioPath'][-1]['question']]['optionalTexts'])
    for optionalTextId in list(optionalTexts):
        condition = True
        noExclusion = True
        if optionalTexts[optionalTextId]['conditionalAnswerId']:
            condition = False
        if optionalTexts[optionalTextId]['exclusionAnswerId']:
            noExclusion = False
        if not condition or not noExclusion:
            noExclusion = True
            for record in session['scenarioPath']:
                if optionalTexts[optionalTextId]['exclusionAnswerId'] == record['question']+"-"+record['answer']:
                    noExclusion = False
                    break
                if not condition and optionalTexts[optionalTextId]['conditionalAnswerId'] == record['question']+"-"+record['answer']:
                    condition = True
        if not condition or not noExclusion:
            del optionalTexts[optionalTextId]

    return render_template('question.html', scenario=scenario, answers=answers, optionalTexts=optionalTexts, questionId=currentQuestion, isGranted=isGranted)


@app.route('/currentStory')
def currentStory():
    global scenarioList, userList

    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))

    if not session.get('scenarioPath'):
        return redirect(url_for('menu'))

    scenario = scenarioList[session['scenarioId']]

    return render_template('currentStory.html', scenario=scenario)


@app.route('/editScenario', methods=['GET', 'POST'])
def editScenario():
    global scenarioList, userList

    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))

    if not session.get('userId'):
        return redirect(url_for('menu'))
    elif userList[session['userId']]['isAdmin']:
        isAdmin = True
    else:
        isAdmin = False

    scenarioId = request.args.get('scenarioId')
    userId = request.args.get('userId')

    if userId and (userId == session['userId'] or isAdmin):
        if scenarioList == {}:
            key = '0'
        else:
            key = str(int(max(scenarioList, key=int)) + 1)
        scenarioList[key] = {'id': key, 'name': 'Nazwa scenariusza', 'user': userId, 'startingQuestion': 'Pytanie startowe', 'goBack': False, 'publicView': False, 'publicEdit': False, 'questions': {}}
        saveToDatabase(key + '.json', {key: scenarioList[key]}, 'scenarios')
        scenarioId = key

    if scenarioId:
        if scenarioId in scenarioList:
            scenario = scenarioList[scenarioId]
            if (scenario['publicView'] and scenario['publicEdit']) or scenario['user'] == session['userId'] or isAdmin:
                session['scenarioId'] = scenarioId
                session['scenarioPath'] = []
                session.pop('questionId', None)
            else:
                return redirect(url_for('menu'))
        else:
            return redirect(url_for('menu'))
    elif session.get('scenarioId') and session['scenarioId'] in scenarioList:
        scenario = scenarioList[session['scenarioId']]
        if (not scenario['publicView'] or not scenario['publicEdit']) and scenario['user'] != session['userId'] and not isAdmin:
            return redirect(url_for('menu'))
    else:
        return redirect(url_for('menu'))

    if request.method == 'POST' and request.form.get('name') and request.form.get('startingQuestion'):
        scenario['name'] = request.form['name']
        scenario['startingQuestion'] = request.form['startingQuestion']
        if request.form.get('goBack'):
            scenario['goBack'] = True
        else:
            scenario['goBack'] = False
        if scenario['user'] == session['userId'] or isAdmin:
            if request.form.get('publicView'):
                scenario['publicView'] = True
            else:
                scenario['publicView'] = False
            if request.form.get('publicEdit'):
                scenario['publicEdit'] = True
            else:
                scenario['publicEdit'] = False
        saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')

    return render_template('editScenario.html', scenario=scenario, isAdmin=isAdmin)


@app.route('/deleteQuestion')
def deleteQuestion():
    global scenarioList, userList

    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))

    if session.get('userId') and session.get('scenarioId') and session['scenarioId'] in scenarioList:
        scenario = scenarioList[session['scenarioId']]
        if (not scenario['publicView'] or not scenario['publicEdit']) and scenario['user'] != session['userId'] and not userList[session['userId']]['isAdmin']:
            return redirect(url_for('menu'))
    else:
        return redirect(url_for('menu'))

    questionId = request.args.get('questionId')

    if not questionId or questionId not in scenario['questions']:
        return redirect(url_for('editScenario'))

    if request.args.get('confirmDelete'):
        del scenario['questions'][questionId]
        saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')
        return redirect(url_for('editScenario'))

    elementName = 'question'
    elementId = questionId
    questionText = scenario['questions'][questionId]['text']

    return render_template('delete.html', elementName=elementName, elementId=elementId, questionText=questionText)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    global scenarioList, userList

    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))

    if session.get('userId') and session.get('scenarioId') and session['scenarioId'] in scenarioList:
        scenario = scenarioList[session['scenarioId']]
        if (not scenario['publicView'] or not scenario['publicEdit']) and scenario['user'] != session['userId'] and not userList[session['userId']]['isAdmin']:
            return redirect(url_for('menu'))
    else:
        return redirect(url_for('menu'))

    questionId = request.args.get('questionId')

    if request.args.get('createQuestion'):
        if scenario['questions'] == {}:
            key = '0'
        else:
            key = str(int(max(scenario['questions'], key=int)) + 1)
        scenario['questions'][key] = {'text': 'Pytanie', 'keyWords': {}, 'optionalTexts': {}, 'answers': {}}
        saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')
        questionId = key

    if questionId:
        if questionId in scenario['questions']:
            session['questionId'] = questionId
        else:
            return redirect(url_for('editScenario'))
    elif not session.get('questionId') or session['questionId'] not in scenario['questions']:
        return redirect(url_for('editScenario'))

    createElement('keyWord', 'Słowo kluczowe', scenario)
    createElement('optionalText', {'text': 'Tekst Opcjonalny', 'conditionalAnswerId': '', 'exclusionAnswerId': ''}, scenario)
    createElement('answer', {'text': 'Odpowiedź', 'questionId': '0', 'conditionalAnswerId': '', 'exclusionAnswerId': ''}, scenario)

    if request.method == 'POST' and request.form.get('text'):
        updateQuestion(scenario)

    return render_template('edit.html', scenario=scenario, questionId=session['questionId'])


@app.route('/delete')
def delete():
    global scenarioList, userList

    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))

    if session.get('userId') and session.get('scenarioId') and session['scenarioId'] in scenarioList and session.get('questionId'):
        scenario = scenarioList[session['scenarioId']]
        if session['questionId'] not in scenario['questions'] or ((not scenario['publicView'] or not scenario['publicEdit']) and scenario['user'] != session['userId'] and not userList[session['userId']]['isAdmin']):
            return redirect(url_for('menu'))
    else:
        return redirect(url_for('menu'))

    if request.args.get('confirmDelete'):
        deleteElement('optionalText', scenario)
        deleteElement('keyWord', scenario)
        deleteElement('answer', scenario)
        return redirect(url_for('edit'))

    question = scenario['questions'][session['questionId']]

    if request.args.get('optionalTextId') and request.args.get('optionalTextId') in question['optionalTexts']:
        elementName = 'optionalText'
        elementId = request.args.get('optionalTextId')
        elementText = question['optionalTexts'][elementId]['text']
    elif request.args.get('keyWordId') and request.args.get('keyWordId') in question['keyWords']:
        elementName = 'keyWord'
        elementId = request.args.get('keyWordId')
        elementText = question['keyWords'][elementId]
    elif request.args.get('answerId') and request.args.get('answerId') in question['answers']:
        elementName = 'answer'
        elementId = request.args.get('answerId')
        elementText = question['answers'][elementId]['text']
    else:
        return redirect(url_for('edit'))

    return render_template('delete.html', elementName=elementName, elementId=elementId, elementText=elementText)


def createElement(element, pattern, scenario):
    "Funkcja stwarzająca dany element"
    if request.args.get(element):
        if scenario['questions'][session['questionId']][element + 's'] == {}:
            key = '0'
        else:
            key = str(int(max(scenario['questions'][session['questionId']][element + 's'], key=int)) + 1)
        scenario['questions'][session['questionId']][element + 's'][key] = pattern
        saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')


def deleteElement(element, scenario):
    "Funkcja usuwająca dany element"
    if request.args.get(element + 'Id') and request.args.get(element + 'Id') in scenario['questions'][session['questionId']][element + 's']:
        del scenario['questions'][session['questionId']][element + 's'][request.args.get(element + 'Id')]
        saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')


def updateQuestion(scenario):
    "Funkcja aktualizująca dane pytania"
    scenario['questions'][session['questionId']]['text'] = request.form['text']
    for key in scenario['questions'][session['questionId']]['keyWords']:
        scenario['questions'][session['questionId']]['keyWords'][key] = request.form['keyWord' + key]
    for key in scenario['questions'][session['questionId']]['optionalTexts']:
        scenario['questions'][session['questionId']]['optionalTexts'][key]['text'] = request.form['optionalText' + key]
        scenario['questions'][session['questionId']]['optionalTexts'][key]['conditionalAnswerId'] = request.form['optionalTextConditionalAnswerId' + key]
        scenario['questions'][session['questionId']]['optionalTexts'][key]['exclusionAnswerId'] = request.form['optionalTextExclusionAnswerId' + key]
    for key in scenario['questions'][session['questionId']]['answers']:
        scenario['questions'][session['questionId']]['answers'][key]['text'] = request.form['answerText' + key]
        scenario['questions'][session['questionId']]['answers'][key]['questionId'] = request.form['answerQuestionId' + key]
        scenario['questions'][session['questionId']]['answers'][key]['conditionalAnswerId'] = request.form['answerConditionalAnswerId' + key]
        scenario['questions'][session['questionId']]['answers'][key]['exclusionAnswerId'] = request.form['answerExclusionAnswerId' + key]
    saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')


def saveToDatabase(name, data, catalog):
    "Funkcja zapisująca dane do bazy"
    with open(PROJECT_ROOT + "/database/" + catalog + "/" + name, "w") as write_file:
        json.dump(data, write_file, indent=4)
    #print(oct(os.stat(PROJECT_ROOT + "/database/" + catalog + "/" + name).st_mode)[-3:])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5035)
