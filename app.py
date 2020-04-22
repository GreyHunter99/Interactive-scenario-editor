from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = 'extra secret key'

scenarioList = {}
userList = {}


@app.route('/')
def menu():
    refreshList('users')
    return render_template('menu.html')


@app.route('/gamebooks')
def gamebooks():
    return render_template('gamebooks.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    global userList
    refreshList('users')
    if request.method == 'POST':
        for user in userList:
            if userList[user]['username'] == request.form['username']:
                if userList[user]['password'] == request.form['password']:
                    session['user'] = user
                    return redirect(url_for('menu'))
                return render_template('login.html', wrongPassword=True)
            return render_template('login.html', wrongUsername=True)
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    global userList
    refreshList('users')
    if request.method == 'POST':
        for user in userList:
            if userList[user]['username'] == request.form['username']:
                return render_template('register.html', usernameTaken=True)
        if userList == {}:
            key = '0'
        else:
            key = str(int(max(userList, key=int))+1)
        userList[key] = {'id': key, 'username': request.form['username'], 'password': request.form['password'], 'description': '', 'isAdmin': False}
        user = {key: userList[key]}
        saveToDatabase(key+'.json', user, 'users')
        session['user'] = key
        refreshList('users')
        return redirect(url_for('menu'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('menu'))


@app.route('/list')
def list():
    global scenarioList

    if request.args.get('deleteScenario'):
        os.remove(PROJECT_ROOT+"/database/scenarios/"+request.args.get('scenarioId')+".json")

    refreshList('scenarios')

    return render_template('list.html', scenarioList=scenarioList)


@app.route('/start', methods=['GET', 'POST'])
def start():
    global scenarioList

    if request.method == 'POST':
        for question in scenarioList[session['scenarioId']]['questions']:
            for keyWord in scenarioList[session['scenarioId']]['questions'][question]['keyWords'].values():
                if keyWord.lower() in request.form['startingQuestion'].lower():
                    return redirect(url_for('question', questionId=question))
        return render_template('start.html', noKeyWords=True)

    session['scenarioPath'] = []

    scenarioId = request.args.get('scenarioId')
    refreshSession(scenarioId)

    return render_template('start.html', scenarioList=scenarioList)


@app.route('/question')
def question():
    global scenarioList
    questionId = request.args.get('questionId')

    if questionId != None and questionId in scenarioList[session['scenarioId']]['questions'].keys():
        scenarioPath = session['scenarioPath']
        scenarioPath.append(questionId)
        session['scenarioPath'] = scenarioPath
    else:
        return redirect(url_for('menu'))

    return render_template('question.html', scenarioList=scenarioList, questionId=questionId)


@app.route('/editScenario', methods=['GET', 'POST'])
def editScenario():
    global scenarioList

    scenarioId = request.args.get('scenarioId')

    if request.args.get('createScenario'):
        if scenarioList == {}:
            key = '0'
        else:
            key = str(int(max(scenarioList, key=int))+1)
        scenarioList[key] = {'id': key, 'name': '', 'userId': session['user'], 'startingQuestion': '', 'questions': {}}
        scenario = {key: scenarioList[key]}
        saveToDatabase(key+'.json', scenario, 'scenarios')
        scenarioId = key

    refreshSession(scenarioId)

    if request.args.get('deleteQuestion'):
        del scenarioList[session['scenarioId']]['questions'][request.args.get('questionId')]
        scenario = {session['scenarioId']: scenarioList[session['scenarioId']]}
        saveToDatabase(session['scenarioId'] + '.json', scenario, 'scenarios')

    if request.method == 'POST':
        scenarioList[session['scenarioId']]['name'] = request.form['name']
        scenarioList[session['scenarioId']]['startingQuestion'] = request.form['startingQuestion']
        scenario = {session['scenarioId']: scenarioList[session['scenarioId']]}
        saveToDatabase(session['scenarioId'] + '.json', scenario, 'scenarios')

    return render_template('editScenario.html', scenarioList=scenarioList)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    global scenarioList

    questionId = request.args.get('questionId')

    refreshSession()

    if request.args.get('createQuestion'):
        if scenarioList[session['scenarioId']]['questions'] == {}:
            key = '0'
        else:
            key = str(int(max(scenarioList[session['scenarioId']]['questions'], key=int)) + 1)
        scenarioList[session['scenarioId']]['questions'][key] = {'text': '', 'keyWords': {}, 'optionalTexts': {}, 'answers': {}}
        scenario = {session['scenarioId']: scenarioList[session['scenarioId']]}
        saveToDatabase(session['scenarioId'] + '.json', scenario, 'scenarios')
        questionId = key

    if request.args.get('createKeyWord'):
        createElement('keyWords', '')

    if request.args.get('deleteKeyWord'):
        deleteElement('keyWord')

    if request.args.get('createOptionalText'):
        createElement('optionalTexts', {'text': '', 'conditionalQuestionId': '', 'exclusionQuestionId': ''})

    if request.args.get('deleteOptionalText'):
        deleteElement('optionalText')

    if request.args.get('createAnswer'):
        createElement('answers', {'text': '', 'questionId': '0', 'conditionalQuestionId': '', 'exclusionQuestionId': ''})

    if request.args.get('deleteAnswer'):
        deleteElement('answer')

    if questionId != None:
        session['questionId'] = questionId
    elif session['questionId'] == None:
        return redirect(url_for('menu'))

    if request.method == 'POST':
        updateQuestion()

    return render_template('edit.html', scenarioList=scenarioList, questionId=session['questionId'])


def createElement(element , pattern):
    "Funkcja stwarzająca dany element"
    global scenarioList
    if scenarioList[session['scenarioId']]['questions'][session['questionId']][element] == {}:
        key = '0'
    else:
        key = str(int(max(scenarioList[session['scenarioId']]['questions'][session['questionId']][element], key=int)) + 1)
    scenarioList[session['scenarioId']]['questions'][session['questionId']][element][key] = pattern
    scenario = {session['scenarioId']: scenarioList[session['scenarioId']]}
    saveToDatabase(session['scenarioId'] + '.json', scenario, 'scenarios')

def deleteElement(element):
    "Funkcja usuwająca dany element"
    global scenarioList
    del scenarioList[session['scenarioId']]['questions'][session['questionId']][element+'s'][request.args.get(element+'Id')]
    scenario = {session['scenarioId']: scenarioList[session['scenarioId']]}
    saveToDatabase(session['scenarioId'] + '.json', scenario, 'scenarios')


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
    scenario = {session['scenarioId']: scenarioList[session['scenarioId']]}
    saveToDatabase(session['scenarioId'] + '.json', scenario, 'scenarios')


def saveToDatabase(name, data, catalog):
    "Funkcja zapisująca dane do bazy"
    with open(PROJECT_ROOT+"/database/"+catalog+"/"+name, "w") as write_file:
        json.dump(data, write_file, indent=4)


def loadFromDatabase(name, catalog):
    "Funkcja wczytująca dane z bazy"
    with open(PROJECT_ROOT+"/database/"+catalog+"/"+name, "r") as read_file:
        data = json.load(read_file)
    return data


def refreshSession(scenarioId=None):
    "Funkcja sprawdzająca poprawność id scenariusza"
    global scenarioList
    if scenarioId != None and scenarioId in scenarioList.keys():
        session['scenarioId'] = scenarioId
    elif session['scenarioId'] == None:
        return redirect(url_for('menu'))


def refreshList(catalog):
    "Funkcja aktualizująca listę scenariuszy"
    global scenarioList, userList
    if catalog == 'users':
        userList = {}
        list = userList
    else:
        scenarioList = {}
        list = scenarioList
    folder = os.listdir(PROJECT_ROOT + "/database/"+catalog+"/")
    folder.sort(key=lambda x: int(x.split(".")[0]))
    for file in folder:
        currentFile = loadFromDatabase(file, catalog)
        list.update(currentFile)


if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port = 5035)
