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
    return render_template('menu.html')


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

    userId = request.args.get('userId')

    if not userId or not session.get('userId') or (userId != session['userId'] and userList[session['userId']]['isAdmin'] is False):
        return redirect(url_for('menu'))

    if request.method == 'POST' and request.form.get('oldPassword') and request.form.get('newPassword') and request.form.get('repeatNewPassword'):
        if request.form['oldPassword'] == userList[userId]['password']:
            if request.form['newPassword'] == request.form['repeatNewPassword']:
                userList[userId]['password'] = request.form['newPassword']
                saveToDatabase(userId + '.json', {userId: userList[userId]}, 'users')
                return redirect(url_for('userProfile', userId=userId))
            else:
                return render_template('changePassword.html', userId=userId, wrongNewPasswords=True)
        else:
            return render_template('changePassword.html', userId=userId, wrongOldPassword=True)

    return render_template('changePassword.html', userId=userId)


@app.route('/grantAdmin')
def grantAdmin():
    global userList
    userId = request.args.get('userId')

    if not userId or not session.get('userId') or userList[session['userId']]['isAdmin'] is False or userId == session.get('userId'):
        return redirect(url_for('menu'))

    if userList[userId]['isAdmin'] is False:
        userList[userId]['isAdmin'] = True
    else:
        userList[userId]['isAdmin'] = False
    saveToDatabase(userId + '.json', {userId: userList[userId]}, 'users')

    return redirect(url_for('userProfile', userId=userId))


@app.route('/deleteUser', methods=['GET', 'POST'])
def deleteUser():
    global scenarioList, userList

    userId = request.args.get('userId')

    if not session.get('userId') or not userId or userId not in userList or (userId != session['userId'] and userList[session['userId']]['isAdmin'] is False):
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
        if isAdmin is True:
            return redirect(url_for('menu'))
        else:
            return redirect(url_for('logout'))

    elementName = 'user'
    elementId = userId

    return render_template('delete.html', userList=userList, elementName=elementName, elementId=elementId)


@app.route('/userProfile', methods=['GET', 'POST'])
def userProfile():
    global scenarioList, userList
    userId = request.args.get('userId')

    if userId and userId in userList:
        pass
    elif session.get('userId'):
        userId = session['userId']
    else:
        return redirect(url_for('menu'))

    if request.method == 'POST' and request.form.get('username') and request.form.get('description') and (userId == session['userId'] or userList[session['userId']]['isAdmin'] is True):
        for user in userList:
            if userList[user]['username'] == request.form['username'] and user != userId:
                return render_template('userProfile.html', scenarioList=scenarioList, userList=userList, userId=userId, usernameTaken=True)
        userList[userId]['username'] = request.form['username']
        userList[userId]['description'] = request.form['description']
        saveToDatabase(userId + '.json', {userId: userList[userId]}, 'users')

    return render_template('userProfile.html', scenarioList=scenarioList, userList=userList, userId=userId)


@app.route('/deleteScenario')
def deleteScenario():
    global scenarioList, userList

    scenarioId = request.args.get('scenarioId')

    if not session.get('userId') or not scenarioId or scenarioId not in scenarioList or (scenarioList[scenarioId]['user'] != session['userId'] and userList[session['userId']]['isAdmin'] is False):
        return redirect(url_for('menu'))

    if request.args.get('confirmDelete'):
        userId = scenarioList[scenarioId]['user']
        del scenarioList[scenarioId]
        os.remove(PROJECT_ROOT + "/database/scenarios/" + scenarioId + ".json")
        return redirect(url_for('userProfile', userId=userId))

    elementName = 'scenario'
    elementId = scenarioId

    return render_template('delete.html', scenarioList=scenarioList, elementName=elementName, elementId=elementId)


@app.route('/scenarios')
def scenarios():
    global scenarioList
    return render_template('scenarios.html', scenarioList=scenarioList)


@app.route('/start', methods=['GET', 'POST'])
def start():
    global scenarioList, userList

    session['scenarioPath'] = []
    session.pop('questionId', None)

    scenarioId = request.args.get('scenarioId')
    if scenarioId:
        if scenarioId in scenarioList:
            session['scenarioId'] = scenarioId
        else:
            return redirect(url_for('menu'))
    elif not session.get('scenarioId') or session['scenarioId'] not in scenarioList:
        return redirect(url_for('scenarios'))

    if request.method == 'POST' and request.form.get('startingQuestion'):
        for questionId in scenarioList[session['scenarioId']]['questions']:
            for keyWord in scenarioList[session['scenarioId']]['questions'][questionId]['keyWords'].values():
                if keyWord.lower() in request.form['startingQuestion'].lower():
                    return redirect(url_for('question', questionId=questionId, keyWord=keyWord))
        return render_template('start.html', scenarioList=scenarioList, noKeyWords=True)

    return render_template('start.html', scenarioList=scenarioList, userList=userList)


@app.route('/question')
def question():
    global scenarioList, userList

    if not session.get('scenarioId') or session['scenarioId'] not in scenarioList:
        return redirect(url_for('scenarios'))

    questionId = request.args.get('questionId')

    if questionId and questionId in scenarioList[session['scenarioId']]['questions']:
        if not session['scenarioPath']:
            if request.args.get('keyWord') and request.args.get('keyWord') in scenarioList[session['scenarioId']]['questions'][questionId]['keyWords'].values():
                session['questionId'] = questionId
                scenarioPath = session['scenarioPath']
                scenarioPath.append(questionId)
                session['scenarioPath'] = scenarioPath
        else:
            for answer in scenarioList[session['scenarioId']]['questions'][session['scenarioPath'][-1]]['answers'].values():
                if answer['questionId'] == questionId:
                    session['questionId'] = questionId
                    scenarioPath = session['scenarioPath']
                    scenarioPath.append(questionId)
                    session['scenarioPath'] = scenarioPath
                    break
        return redirect(url_for('question'))
    elif not session.get('questionId') or session['questionId'] not in scenarioList[session['scenarioId']]['questions']:
        return redirect(url_for('menu'))

    return render_template('question.html', scenarioList=scenarioList, userList=userList , questionId=session['questionId'])


@app.route('/editScenario', methods=['GET', 'POST'])
def editScenario():
    global scenarioList, userList

    if not session.get('userId'):
        return redirect(url_for('menu'))

    scenarioId = request.args.get('scenarioId')
    userId = request.args.get('userId')

    if userId and (userId == session['userId'] or userList[session['userId']]['isAdmin'] is True):
        if scenarioList == {}:
            key = '0'
        else:
            key = str(int(max(scenarioList, key=int)) + 1)
        scenarioList[key] = {'id': key, 'name': '', 'user': userId, 'startingQuestion': '', 'questions': {}}
        saveToDatabase(key + '.json', {key: scenarioList[key]}, 'scenarios')
        scenarioId = key

    if scenarioId:
        if scenarioId in scenarioList and (scenarioList[scenarioId]['user'] == session['userId'] or userList[session['userId']]['isAdmin'] is True):
            session['scenarioId'] = scenarioId
            session['scenarioPath'] = []
            session.pop('questionId', None)
        else:
            return redirect(url_for('menu'))
    elif not session.get('scenarioId') or session['scenarioId'] not in scenarioList or (scenarioList[session['scenarioId']]['user'] != session['userId'] and userList[session['userId']]['isAdmin'] is False):
        return redirect(url_for('userProfile'))

    if request.method == 'POST' and request.form.get('name') and request.form.get('startingQuestion'):
        scenarioList[session['scenarioId']]['name'] = request.form['name']
        scenarioList[session['scenarioId']]['startingQuestion'] = request.form['startingQuestion']
        saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenarioList[session['scenarioId']]}, 'scenarios')

    return render_template('editScenario.html', scenarioList=scenarioList)


@app.route('/deleteQuestion')
def deleteQuestion():
    global scenarioList, userList

    if not session.get('userId') or not session.get('scenarioId') or session['scenarioId'] not in scenarioList or (scenarioList[session['scenarioId']]['user'] != session['userId'] and userList[session['userId']]['isAdmin'] is False):
        return redirect(url_for('menu'))

    questionId = request.args.get('questionId')

    if not questionId or questionId not in scenarioList[session['scenarioId']]['questions']:
        return redirect(url_for('editScenario'))

    if request.args.get('confirmDelete'):
        del scenarioList[session['scenarioId']]['questions'][questionId]
        saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenarioList[session['scenarioId']]}, 'scenarios')
        return redirect(url_for('editScenario'))

    elementName = 'question'
    elementId = questionId

    return render_template('delete.html', scenarioList=scenarioList, elementName=elementName, elementId=elementId)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    global scenarioList, userList

    if not session.get('userId') or not session.get('scenarioId') or session['scenarioId'] not in scenarioList or (scenarioList[session['scenarioId']]['user'] != session['userId'] and userList[session['userId']]['isAdmin'] is False):
        return redirect(url_for('menu'))

    questionId = request.args.get('questionId')

    if request.args.get('createQuestion'):
        if scenarioList[session['scenarioId']]['questions'] == {}:
            key = '0'
        else:
            key = str(int(max(scenarioList[session['scenarioId']]['questions'], key=int)) + 1)
        scenarioList[session['scenarioId']]['questions'][key] = {'text': '', 'keyWords': {}, 'optionalTexts': {}, 'answers': {}}
        saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenarioList[session['scenarioId']]}, 'scenarios')
        questionId = key

    if questionId:
        if questionId in scenarioList[session['scenarioId']]['questions']:
            session['questionId'] = questionId
        else:
            return redirect(url_for('editScenario'))
    elif not session.get('questionId') or session['questionId'] not in scenarioList[session['scenarioId']]['questions']:
        return redirect(url_for('editScenario'))

    createElement('keyWord', '')
    createElement('optionalText', {'text': '', 'conditionalQuestionId': '', 'exclusionQuestionId': ''})
    createElement('answer', {'text': '', 'questionId': '0', 'conditionalQuestionId': '', 'exclusionQuestionId': ''})

    if request.method == 'POST' and request.form.get('text'):
        updateQuestion()

    return render_template('edit.html', scenarioList=scenarioList, questionId=session['questionId'])


@app.route('/delete')
def delete():
    global scenarioList, userList

    if not session.get('userId') or not session.get('scenarioId') or session['scenarioId'] not in scenarioList or not session.get('questionId') or session['questionId'] not in scenarioList[session['scenarioId']]['questions'] or (scenarioList[session['scenarioId']]['user'] != session['userId'] and userList[session['userId']]['isAdmin'] is False):
        return redirect(url_for('menu'))

    if request.args.get('confirmDelete'):
        deleteElement('optionalText')
        deleteElement('keyWord')
        deleteElement('answer')
        return redirect(url_for('edit'))

    if request.args.get('optionalTextId') and request.args.get('optionalTextId') in scenarioList[session['scenarioId']]['questions'][session['questionId']]['optionalTexts']:
        elementName = 'optionalText'
        elementId = request.args.get('optionalTextId')
    elif request.args.get('keyWordId') and request.args.get('keyWordId') in scenarioList[session['scenarioId']]['questions'][session['questionId']]['keyWords']:
        elementName = 'keyWord'
        elementId = request.args.get('keyWordId')
    elif request.args.get('answerId') and request.args.get('answerId') in scenarioList[session['scenarioId']]['questions'][session['questionId']]['answers']:
        elementName = 'answer'
        elementId = request.args.get('answerId')
    else:
        return redirect(url_for('edit'))

    return render_template('delete.html', scenarioList=scenarioList, elementName=elementName, elementId=elementId)


def createElement(element, pattern):
    "Funkcja stwarzająca dany element"
    global scenarioList
    if request.args.get(element):
        if scenarioList[session['scenarioId']]['questions'][session['questionId']][element + 's'] == {}:
            key = '0'
        else:
            key = str(int(max(scenarioList[session['scenarioId']]['questions'][session['questionId']][element + 's'], key=int)) + 1)
        scenarioList[session['scenarioId']]['questions'][session['questionId']][element + 's'][key] = pattern
        saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenarioList[session['scenarioId']]}, 'scenarios')


def deleteElement(element):
    "Funkcja usuwająca dany element"
    global scenarioList
    if request.args.get(element + 'Id') and request.args.get(element + 'Id') in scenarioList[session['scenarioId']]['questions'][session['questionId']][element + 's']:
        del scenarioList[session['scenarioId']]['questions'][session['questionId']][element + 's'][request.args.get(element + 'Id')]
        saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenarioList[session['scenarioId']]}, 'scenarios')


def updateQuestion():
    "Funkcja aktualizująca dane pytania"
    global scenarioList
    scenarioList[session['scenarioId']]['questions'][session['questionId']]['text'] = request.form['text']
    for key in scenarioList[session['scenarioId']]['questions'][session['questionId']]['keyWords']:
        scenarioList[session['scenarioId']]['questions'][session['questionId']]['keyWords'][key] = request.form['keyWord' + key]
    for key in scenarioList[session['scenarioId']]['questions'][session['questionId']]['optionalTexts']:
        scenarioList[session['scenarioId']]['questions'][session['questionId']]['optionalTexts'][key]['text'] = request.form['optionalText' + key]
        scenarioList[session['scenarioId']]['questions'][session['questionId']]['optionalTexts'][key]['conditionalQuestionId'] = request.form['optionalTextConditionalQuestionId' + key]
        scenarioList[session['scenarioId']]['questions'][session['questionId']]['optionalTexts'][key]['exclusionQuestionId'] = request.form['optionalTextExclusionQuestionId' + key]
    for key in scenarioList[session['scenarioId']]['questions'][session['questionId']]['answers']:
        scenarioList[session['scenarioId']]['questions'][session['questionId']]['answers'][key]['text'] = request.form['answerText' + key]
        scenarioList[session['scenarioId']]['questions'][session['questionId']]['answers'][key]['questionId'] = request.form['answerQuestionId' + key]
        scenarioList[session['scenarioId']]['questions'][session['questionId']]['answers'][key]['conditionalQuestionId'] = request.form['answerConditionalQuestionId' + key]
        scenarioList[session['scenarioId']]['questions'][session['questionId']]['answers'][key]['exclusionQuestionId'] = request.form['answerExclusionQuestionId' + key]
    saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenarioList[session['scenarioId']]}, 'scenarios')


def saveToDatabase(name, data, catalog):
    "Funkcja zapisująca dane do bazy"
    with open(PROJECT_ROOT + "/database/" + catalog + "/" + name, "w") as write_file:
        json.dump(data, write_file, indent=4)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5035)
