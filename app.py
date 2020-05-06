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
    if noUserInDatabase():
        return noUserInDatabase()

    return render_template('menu.html', isGranted=isGranted())


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

    if noUserInDatabase():
        return noUserInDatabase()

    userId = request.args.get('userId')

    if not userId or (not isGranted(userId=userId) and not isGranted()):
        return redirect(url_for('menu'))

    if isGranted() and not isGranted(userId=userId):
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

    if noUserInDatabase():
        return noUserInDatabase()

    userId = request.args.get('userId')

    if not userId or not isGranted() or isGranted(userId=userId):
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

    if noUserInDatabase():
        return noUserInDatabase()

    if not isGranted():
        return redirect(url_for('menu'))

    return render_template('users.html', userList=userList)


@app.route('/deleteUser', methods=['GET', 'POST'])
def deleteUser():
    global scenarioList, userList

    if noUserInDatabase():
        return noUserInDatabase()

    userId = request.args.get('userId')

    if not userId or userId not in userList or (not isGranted(userId=userId) and not isGranted()):
        return redirect(url_for('menu'))

    if request.args.get('confirmDelete') and request.method == 'POST' and request.form.get('deleteUserScenarios'):
        userIsAdmin = isGranted()
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
        if userIsAdmin:
            return redirect(url_for('menu'))
        else:
            return redirect(url_for('logout'))

    elementData = {'name': 'user', 'id': userId, 'username': userList[userId]['username']}

    return render_template('delete.html', elementData=elementData)


@app.route('/userProfile', methods=['GET', 'POST'])
def userProfile():
    global scenarioList, userList

    if noUserInDatabase():
        return noUserInDatabase()

    userId = request.args.get('userId')

    if userId and userId in userList:
        pass
    elif session.get('userId'):
        userId = session['userId']
    else:
        return redirect(url_for('menu'))

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

    if request.method == 'POST' and request.form.get('username') and request.form.get('description') is not None and (isGranted(userId=userId) or isGranted()):
        for user in userList:
            if userList[user]['username'] == request.form['username'] and user != userId:
                return render_template('userProfile.html', isAdmin=isGranted(), isProfileOwner=isGranted(userId=userId), userScenarioList=userScenarioList, userData=userData, usernameTaken=True)
        userList[userId]['username'] = request.form['username']
        userList[userId]['description'] = request.form['description']
        saveToDatabase(userId + '.json', {userId: userList[userId]}, 'users')
        userData = dict(userList[userId])
        del userData['password']

    return render_template('userProfile.html', isAdmin=isGranted(), isProfileOwner=isGranted(userId=userId), userScenarioList=userScenarioList, userData=userData)


@app.route('/deleteScenario')
def deleteScenario():
    global scenarioList

    if noUserInDatabase():
        return noUserInDatabase()

    scenarioId = request.args.get('scenarioId')

    if not scenarioId or scenarioId not in scenarioList or not isGranted(scenario=scenarioList[scenarioId]):
        return redirect(url_for('menu'))

    scenario = scenarioList[scenarioId]

    if request.args.get('confirmDelete'):
        userId = scenario['user']
        del scenarioList[scenarioId]
        os.remove(PROJECT_ROOT + "/database/scenarios/" + scenarioId + ".json")
        return redirect(url_for('userProfile', userId=userId))

    elementData = {'name': 'scenario', 'id': scenarioId, 'scenarioName': scenario['name'], 'scenarioOwner': scenario['user']}

    return render_template('delete.html', elementData=elementData)


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

    if noUserInDatabase():
        return noUserInDatabase()

    scenarioId = request.args.get('scenarioId')

    if scenarioId:
        if scenarioId in scenarioList:
            if scenarioList[scenarioId]['publicView'] or isGranted(scenario=scenarioList[scenarioId]):
                session['scenarioId'] = scenarioId
                session.pop('questionId', None)
            else:
                return redirect(url_for('menu'))
        else:
            return redirect(url_for('menu'))
    elif checkScenarioSession(story='scenarios'):
        return checkScenarioSession(story='scenarios')
    scenario = scenarioList[session['scenarioId']]

    session['scenarioPath'] = []
    session.pop('startingAnswer', None)

    if scenario['user'] in userList:
        ownerExists = True
    else:
        ownerExists = False

    if request.method == 'POST' and request.form.get('startingAnswer'):
        for questionId in scenario['questions']:
            for keyWord in scenario['questions'][questionId]['keyWords'].values():
                if keyWord.lower() in request.form['startingAnswer'].lower():
                    scenarioPath = session['scenarioPath']
                    scenarioPath.append(questionId)
                    session['scenarioPath'] = scenarioPath
                    session['startingAnswer'] = request.form['startingAnswer']
                    return redirect(url_for('question'))
        return render_template('start.html', scenario=scenario, isGranted=isGranted(scenario=scenario, publicEdit=True), ownerExists=ownerExists, noKeyWords=True)

    return render_template('start.html', scenario=scenario, isGranted=isGranted(scenario=scenario, publicEdit=True), ownerExists=ownerExists)


@app.route('/question')
def question():
    global scenarioList

    if noUserInDatabase():
        return noUserInDatabase()

    if checkScenarioSession(story='start'):
        return checkScenarioSession(story='start')
    scenario = scenarioList[session['scenarioId']]

    questionId = request.args.get('questionId')
    answerId = request.args.get('answerId')

    if questionId and questionId in scenario['questions'] and answerId and session['scenarioPath']:
        answers = scenario['questions'][session['scenarioPath'][-1].split("-")[0]]['answers']
        if answerId in answers:
            answer = answers[answerId]
            if answer['questionId'] == questionId:
                if checkRequirements(answer):
                    scenarioPath = session['scenarioPath']
                    scenarioPath.append(questionId)
                    scenarioPath[-2] += "-"+answerId
                    session['scenarioPath'] = scenarioPath
        return redirect(url_for('question'))

    if request.args.get('goBack') and scenario['goBack'] and session['scenarioPath']:
        scenarioPath = session['scenarioPath']
        scenarioPath.pop()
        if session['scenarioPath']:
            scenarioPath[-1] = scenarioPath[-1].split("-")[0]
        session['scenarioPath'] = scenarioPath
        return redirect(url_for('question'))

    if session['scenarioPath'] and session['scenarioPath'][-1].split("-")[0] in scenario['questions']:
        currentQuestion = session['scenarioPath'][-1].split("-")[0]
    else:
        return redirect(url_for('start'))

    answers = dict(scenario['questions'][session['scenarioPath'][-1].split("-")[0]]['answers'])
    for answerId in list(answers):
        if not checkRequirements(answers[answerId]):
            del answers[answerId]

    optionalTexts = dict(scenario['questions'][session['scenarioPath'][-1].split("-")[0]]['optionalTexts'])
    for optionalTextId in list(optionalTexts):
        if not checkRequirements(optionalTexts[optionalTextId]):
            del optionalTexts[optionalTextId]

    return render_template('question.html', scenario=scenario, answers=answers, optionalTexts=optionalTexts, questionId=currentQuestion, isGranted=isGranted(scenario=scenario, publicEdit=True))


@app.route('/currentStory')
def currentStory():
    global scenarioList

    if noUserInDatabase():
        return noUserInDatabase()

    if not session.get('scenarioPath'):
        return redirect(url_for('menu'))

    scenario = scenarioList[session['scenarioId']]

    return render_template('currentStory.html', scenario=scenario)


@app.route('/editScenario', methods=['GET', 'POST'])
def editScenario():
    global scenarioList

    if noUserInDatabase():
        return noUserInDatabase()

    if not session.get('userId'):
        return redirect(url_for('menu'))

    scenarioId = request.args.get('scenarioId')
    userId = request.args.get('userId')

    if userId:
        if isGranted(userId=userId) or isGranted():
            if scenarioList == {}:
                key = '0'
            else:
                key = str(int(max(scenarioList, key=int)) + 1)
            scenarioList[key] = {'id': key, 'name': 'Nazwa scenariusza', 'user': userId, 'startingQuestion': 'Pytanie startowe', 'goBack': False, 'publicView': False, 'publicEdit': False, 'questions': {}}
            saveToDatabase(key + '.json', {key: scenarioList[key]}, 'scenarios')
            scenarioId = key
        else:
            return redirect(url_for('userProfile'))

    if scenarioId:
        if scenarioId in scenarioList:
            if isGranted(scenario=scenarioList[scenarioId], publicEdit=True):
                session['scenarioId'] = scenarioId
                session['scenarioPath'] = []
                session.pop('startingAnswer', None)
                session.pop('questionId', None)
            else:
                return redirect(url_for('menu'))
        else:
            return redirect(url_for('menu'))
    elif checkScenarioSession():
        return checkScenarioSession()
    scenario = scenarioList[session['scenarioId']]

    if request.method == 'POST' and request.form.get('name') and request.form.get('startingQuestion'):
        scenario['name'] = request.form['name']
        scenario['startingQuestion'] = request.form['startingQuestion']
        if request.form.get('goBack'):
            scenario['goBack'] = True
        else:
            scenario['goBack'] = False
        if isGranted(scenario=scenario):
            if request.form.get('publicView'):
                scenario['publicView'] = True
            else:
                scenario['publicView'] = False
            if request.form.get('publicEdit'):
                scenario['publicEdit'] = True
            else:
                scenario['publicEdit'] = False
        saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')

    return render_template('editScenario.html', scenario=scenario, isGranted=isGranted(scenario=scenario))


@app.route('/deleteQuestion')
def deleteQuestion():
    global scenarioList

    if noUserInDatabase():
        return noUserInDatabase()

    if checkScenarioSession():
        return checkScenarioSession()
    scenario = scenarioList[session['scenarioId']]

    questionId = request.args.get('questionId')

    if not questionId or questionId not in scenario['questions']:
        return redirect(url_for('editScenario'))

    if request.args.get('confirmDelete'):
        del scenario['questions'][questionId]
        saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')
        return redirect(url_for('editScenario'))

    elementData = {'name': 'question', 'id': questionId, 'questionText': scenario['questions'][questionId]['text']}

    return render_template('delete.html', elementData=elementData)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    global scenarioList

    if noUserInDatabase():
        return noUserInDatabase()

    if checkScenarioSession():
        return checkScenarioSession()
    scenario = scenarioList[session['scenarioId']]

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
    createElement('optionalText', {'text': 'Tekst Opcjonalny', 'conditionalAnswers': [], 'exclusionAnswers': []}, scenario)
    createElement('answer', {'text': 'Odpowiedź', 'questionId': '0', 'conditionalAnswers': [], 'exclusionAnswers': []}, scenario)

    if request.args.get('requirement'):
        requirement = request.args.get('requirement').split("-")
        if len(requirement) > 4:
            deleteRequirement(requirement, scenario)
        else:
            createRequirement(requirement, scenario)

    if request.method == 'POST' and request.form.get('text'):
        updateQuestion(scenario)

    return render_template('edit.html', scenario=scenario, questionId=session['questionId'])


@app.route('/delete')
def delete():
    global scenarioList

    if noUserInDatabase():
        return noUserInDatabase()

    if checkScenarioSession():
        return checkScenarioSession()
    scenario = scenarioList[session['scenarioId']]

    if not session.get('questionId') or session['questionId'] not in scenario['questions']:
        return redirect(url_for('menu'))

    if request.args.get('confirmDelete'):
        deleteElement(request.args.get('confirmDelete'), scenario)
        return redirect(url_for('edit'))

    editedQuestion = scenario['questions'][session['questionId']]

    if request.args.get('optionalTextId') and request.args.get('optionalTextId') in editedQuestion['optionalTexts']:
        elementData = {'name': 'optionalText', 'id': request.args.get('optionalTextId'), 'text': editedQuestion['optionalTexts'][request.args.get('optionalTextId')]['text']}
    elif request.args.get('keyWordId') and request.args.get('keyWordId') in editedQuestion['keyWords']:
        elementData = {'name': 'keyWord', 'id': request.args.get('keyWordId'), 'text': editedQuestion['keyWords'][request.args.get('keyWordId')]}
    elif request.args.get('answerId') and request.args.get('answerId') in editedQuestion['answers']:
        elementData = {'name': 'answer', 'id': request.args.get('answerId'), 'text': editedQuestion['answers'][request.args.get('answerId')]['text']}
    else:
        return redirect(url_for('edit'))

    return render_template('delete.html', elementData=elementData)


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
    if element == 'optionalText' or element == 'keyWord' or element == 'answer':
        if request.args.get(element + 'Id') and request.args.get(element + 'Id') in scenario['questions'][session['questionId']][element + 's']:
            del scenario['questions'][session['questionId']][element + 's'][request.args.get(element + 'Id')]
            saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')


def createRequirement(requirement, scenario):
    "Funkcja stwarzająca wymaganie do danego elementu"
    if (requirement[0] == 'optionalTexts' or requirement[0] == 'answers') and (requirement[1] == 'conditionalAnswers' or requirement[1] == 'exclusionAnswers'):
        if requirement[2] in scenario['questions'][session['questionId']][requirement[0]]:
            scenario['questions'][session['questionId']][requirement[0]][requirement[2]][requirement[1]].append("0-0")
            saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')


def deleteRequirement(requirement, scenario):
    "Funkcja usuwająca wymaganie do danego elementu"
    if (requirement[0] == 'optionalTexts' or requirement[0] == 'answers') and (requirement[1] == 'conditionalAnswers' or requirement[1] == 'exclusionAnswers'):
        if requirement[2] in scenario['questions'][session['questionId']][requirement[0]]:
            if requirement[3].isdigit() and int(requirement[3]) < len(scenario['questions'][session['questionId']][requirement[0]][requirement[2]][requirement[1]]):
                del scenario['questions'][session['questionId']][requirement[0]][requirement[2]][requirement[1]][int(requirement[3])]
                saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')


def updateQuestion(scenario):
    "Funkcja aktualizująca dane pytania"
    scenario['questions'][session['questionId']]['text'] = request.form['text']
    for keyWordKey in scenario['questions'][session['questionId']]['keyWords']:
        scenario['questions'][session['questionId']]['keyWords'][keyWordKey] = request.form['keyWord' + keyWordKey]
    for optionalTextKey, optionalText in scenario['questions'][session['questionId']]['optionalTexts'].items():
        optionalText['text'] = request.form['optionalText' + optionalTextKey]
        for requirementKey in range(len(optionalText['conditionalAnswers'])):
            optionalText['conditionalAnswers'][requirementKey] = request.form['optionalText' + optionalTextKey + 'ConditionalAnswers' + str(requirementKey)]
        for requirementKey in range(len(optionalText['exclusionAnswers'])):
            optionalText['exclusionAnswers'][requirementKey] = request.form['optionalText' + optionalTextKey + 'ExclusionAnswers' + str(requirementKey)]
    for answerKey, answer in scenario['questions'][session['questionId']]['answers'].items():
        answer['text'] = request.form['answerText' + answerKey]
        answer['questionId'] = request.form['answerQuestionId' + answerKey]
        for requirementKey in range(len(answer['conditionalAnswers'])):
            answer['conditionalAnswers'][requirementKey] = request.form['answer' + answerKey + 'ConditionalAnswers' + str(requirementKey)]
        for requirementKey in range(len(answer['exclusionAnswers'])):
            answer['exclusionAnswers'][requirementKey] = request.form['answer' + answerKey + 'ExclusionAnswers' + str(requirementKey)]
    saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')


def checkRequirements(element):
    "Funkcja sprawdzająca wymagania danego elementu"
    condition = True
    noExclusion = True
    if element['conditionalAnswers']:
        condition = False
    if element['exclusionAnswers']:
        noExclusion = False
    if not condition or not noExclusion:
        noExclusion = True
        for record in session['scenarioPath']:
            if record in element['exclusionAnswers']:
                noExclusion = False
                break
            if not condition and record in element['conditionalAnswers']:
                condition = True
    if condition and noExclusion:
        return True


def noUserInDatabase():
    "Funkcja sprawdzająca czy zalogowany użytkownik znajduje się w bazie"
    global userList
    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))


def checkScenarioSession(story=None):
    "Funkcja sprawdzająca zmienną sesyjną przechowująca id scenariusza"
    global scenarioList
    if session.get('scenarioId') and session['scenarioId'] in scenarioList:
        if story:
            if not scenarioList[session['scenarioId']]['publicView'] and not isGranted(scenario=scenarioList[session['scenarioId']]):
                return redirect(url_for(story))
        else:
            if not isGranted(scenario=scenarioList[session['scenarioId']], publicEdit=True):
                return redirect(url_for('menu'))
    elif story:
        return redirect(url_for(story))
    else:
        return redirect(url_for('menu'))


def isGranted(scenario=None, userId=None, publicEdit=None):
    "Funkcja zwracająca rolę zalogowanego użytkownika"
    global userList
    if session.get('userId'):
        if userId:
            if userId == session['userId']:
                return 'profileOwner'
        else:
            if userList[session['userId']]['isAdmin']:
                return 'admin'
            if scenario:
                if scenario['user'] == session['userId']:
                    return 'owner'
                if publicEdit:
                    if scenario['publicView'] and scenario['publicEdit']:
                        return 'granted'


def saveToDatabase(name, data, catalog):
    "Funkcja zapisująca dane do bazy"
    with open(PROJECT_ROOT + "/database/" + catalog + "/" + name, "w") as write_file:
        json.dump(data, write_file, indent=4)
    #print(oct(os.stat(PROJECT_ROOT + "/database/" + catalog + "/" + name).st_mode)[-3:])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5035)
