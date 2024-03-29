from flask import Flask, render_template, request, redirect, url_for, session, flash
from passlib.hash import sha256_crypt
import json
import os
import copy

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = 'secret key'


@app.route('/')
def menu():
    "Menu główne."
    try:
        if noUserInDatabase():
            return noUserInDatabase()
        return render_template('menu.html', isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/instructions')
def instructions():
    "Podstrona z instukcjami do aplikacji."
    try:
        if noUserInDatabase():
            return noUserInDatabase()
        return render_template('instructions.html', isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/info')
def info():
    "Podstrona o serwisie."
    try:
        if noUserInDatabase():
            return noUserInDatabase()
        return render_template('info.html', isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    "Logowanie."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        if session.get('userId'):
            return redirect(url_for('menu'))

        if request.method == 'POST' and request.form.get('username') and request.form.get('password'):
            userList = loadList('users')
            for user in userList:
                if userList[user]['username'] == request.form['username']:
                    if sha256_crypt.verify(request.form['password'], userList[user]['password']):
                        session.clear()
                        session['userId'] = user
                        flash('Zalogowano')
                        return redirect(url_for('menu'))
                    flash('Złe hasło', 'error')
                    return redirect(url_for('login'))
            flash('Zła nazwa użytkownika', 'error')
            return redirect(url_for('login'))

        return render_template('login.html', isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    "Rejestracja."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        if session.get('userId'):
            return redirect(url_for('menu'))

        if request.method == 'POST' and request.form.get('username') and request.form.get('password') and request.form.get('repeatPassword'):
            userList = loadList('users')
            correctForm = True
            for user in userList:
                if userList[user]['username'] == request.form['username']:
                    flash('Nazwa użytkownika zajęta', 'error')
                    correctForm = False
                    break
            if len(request.form['username']) < 4 or len(request.form['username']) > 30:
                flash('Nazwa użytkownika musi mieć od 4 do 30 znaków', 'error')
                correctForm = False
            if len(request.form['password']) < 4 or len(request.form['password']) > 30:
                flash('Hasło musi mieć od 4 do 30 znaków', 'error')
                correctForm = False
            if request.form['password'] != request.form['repeatPassword']:
                flash('Hasła są różne', 'error')
                correctForm = False
            if correctForm:
                if userList == {}:
                    key = '0'
                else:
                    key = str(int(max(userList, key=int)) + 1)
                user = {'id': key, 'username': request.form['username'], 'password': sha256_crypt.encrypt(request.form['password']), 'description': '', 'isAdmin': False}
                saveToDatabase(key + '.json', {key: user}, 'users')
                session.clear()
                session['userId'] = key
                flash('Zarejestrowano')
                return redirect(url_for('menu'))
            return redirect(url_for('register'))

        return render_template('register.html', isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/logout')
def logout():
    "Wylogowanie."
    try:
        if session.get('userId'):
            session.clear()
            flash('Wylogowano')
            if request.args.get('accountDelete'):
                flash('Usunięto konto użytkownika', 'delete')
                if request.args.get('accountDelete').split("-")[0] == 'yes':
                    flash('Usunięto scenariusze użytkownika', 'delete')
                else:
                    flash('Zachowano scenariusze użytkownika')
                if request.args.get('accountDelete').split("-")[1] == 'yes':
                    flash('Usunięto historie użytkownika', 'delete')
                else:
                    flash('Zachowano historie użytkownika')
        return redirect(url_for('menu'))
    except:
        return redirect(url_for('menu'))


@app.route('/changePassword', methods=['GET', 'POST'])
def changePassword():
    "Zmiana hasła."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        userId = request.args.get('userId')
        userList = loadList('users')

        if not userId or userId not in userList or (not isGranted(userId=userId) and not isGranted()):
            return redirect(url_for('menu'))

        "Warunek na niewymaganie starego hasła."
        if isGranted() and not isGranted(userId=userId):
            noOldPassword = True
        else:
            noOldPassword = False

        if request.method == 'POST' and request.form.get('newPassword') and request.form.get('repeatNewPassword') and (noOldPassword or request.form.get('oldPassword')):
            correctForm = True
            if not noOldPassword and not sha256_crypt.verify(request.form['oldPassword'], userList[userId]['password']):
                flash('Złe stare hasło', 'error')
                correctForm = False
            if len(request.form['newPassword']) < 4 or len(request.form['newPassword']) > 30:
                flash('Nowe hasło musi mieć od 4 do 30 znaków', 'error')
                correctForm = False
            if request.form['newPassword'] != request.form['repeatNewPassword']:
                flash('Nowe hasła się nie zgadzają', 'error')
                correctForm = False
            if correctForm:
                userList[userId]['password'] = sha256_crypt.encrypt(request.form['newPassword'])
                saveToDatabase(userId + '.json', {userId: userList[userId]}, 'users')
                flash('Hasło zostało zmienione')
                return redirect(url_for('userProfile', userId=userId))
            return redirect(url_for('changePassword', userId=userId))

        return render_template('changePassword.html', noOldPassword=noOldPassword, userId=userId, isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/grantAdmin')
def grantAdmin():
    "Nadawanie lub odbieranie praw administratora."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        userId = request.args.get('userId')
        userList = loadList('users')

        if not userId or userId not in userList or not isGranted() or isGranted(userId=userId):
            return redirect(url_for('menu'))

        if not userList[userId]['isAdmin']:
            userList[userId]['isAdmin'] = True
            flash('Nadano uprawnienia administratora')
        else:
            userList[userId]['isAdmin'] = False
            flash('Odebrano uprawnienia administratora', 'delete')
        saveToDatabase(userId + '.json', {userId: userList[userId]}, 'users')

        return redirect(url_for('userProfile', userId=userId))
    except:
        return redirect(url_for('menu'))


@app.route('/users')
def users():
    "Lista użytkowników - tylko dla administratorów."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        if not isGranted():
            return redirect(url_for('menu'))

        userList = loadList('users')

        return render_template('users.html', userList=userList, isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/deleteUser', methods=['GET', 'POST'])
def deleteUser():
    "Usuwanie konta użytkownika."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        userId = request.args.get('userId')
        userList = loadList('users')

        if not userId or userId not in userList or (not isGranted(userId=userId) and not isGranted()):
            return redirect(url_for('menu'))

        "Potwierdzenie usunięcia."
        if request.args.get('confirmDelete') and request.method == 'POST' and request.form.get('deleteUserScenarios') and request.form.get('deleteUserStories'):
            userIsAdmin = isGranted()
            "Usunięcie lub zmiana danych scenariuszy usuwanego użytkownika."
            scenarioList = loadList('scenarios')
            storyList = loadList('stories')
            for scenarioId in scenarioList:
                if scenarioList[scenarioId]['user'] == userId:
                    if request.form['deleteUserScenarios'] == 'Yes':
                        "Zmiana danych historii na podstawie usuwanego scenariusza."
                        for storyId in storyList:
                            if storyList[storyId]['scenario'] == scenarioId:
                                storyList[storyId]['scenario'] = ''
                                saveToDatabase(storyId + '.json', {storyId: storyList[storyId]}, 'stories')
                        os.remove(PROJECT_ROOT + "/database/scenarios/" + scenarioId + ".json")
                    else:
                        scenarioList[scenarioId]['user'] = ''
                        saveToDatabase(scenarioId + '.json', {scenarioId: scenarioList[scenarioId]}, 'scenarios')
            "Usunięcie lub zmiana danych historii usuwanego użytkownika."
            for storyId in storyList:
                if storyList[storyId]['user'] == userId:
                    if request.form['deleteUserStories'] == 'Yes':
                        os.remove(PROJECT_ROOT + "/database/stories/" + storyId + ".json")
                    else:
                        storyList[storyId]['user'] = ''
                        if storyList[storyId]['owner'] == userId:
                            storyList[storyId]['owner'] = ''
                        saveToDatabase(storyId + '.json', {storyId: storyList[storyId]}, 'stories')
                elif storyList[storyId]['owner'] == userId:
                    storyList[storyId]['owner'] = ''
                    saveToDatabase(storyId + '.json', {storyId: storyList[storyId]}, 'stories')
            os.remove(PROJECT_ROOT + "/database/users/" + userId + ".json")
            flash('Usunięto konto użytkownika', 'delete')
            if request.form['deleteUserScenarios'] == 'Yes':
                flash('Usunięto scenariusze użytkownika', 'delete')
                accountDelete = 'yes-'
            else:
                flash('Zachowano scenariusze użytkownika')
                accountDelete = 'no-'
            if request.form['deleteUserStories'] == 'Yes':
                flash('Usunięto historie użytkownika', 'delete')
                accountDelete += 'yes'
            else:
                flash('Zachowano historie użytkownika')
                accountDelete += 'no'
            if userIsAdmin:
                return redirect(url_for('menu'))
            else:
                return redirect(url_for('logout', accountDelete=accountDelete))

        elementData = {'name': 'user', 'id': userId, 'username': userList[userId]['username']}

        return render_template('delete.html', elementData=elementData, isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/userProfile', methods=['GET', 'POST'])
def userProfile():
    "Profil użytkownika."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        userId = request.args.get('userId')
        userList = loadList('users')

        if userId and userId in userList:
            pass
        elif session.get('userId'):
            userId = session['userId']
        else:
            return redirect(url_for('menu'))

        userData = dict(userList[userId])
        del userData['password']

        "Stworzenie listy scenariuszy użytkownika do wyświetlenia na profilu."
        scenarioList = loadList('scenarios')
        userScenarioList = {'privateScenarios': {}, 'publicScenarios': {}, 'publicEditScenarios': {}}
        for key, scenario in scenarioList.items():
            if scenario['user'] == userId:
                if not scenario['publicView']:
                    if isGranted(userId=userId) or isGranted():
                        userScenarioList['privateScenarios'][key] = scenario['name']
                elif scenario['publicEdit']:
                    userScenarioList['publicEditScenarios'][key] = scenario['name']
                else:
                    userScenarioList['publicScenarios'][key] = scenario['name']

        "Stworzenie listy historii użytkownika do wyświetlenia na profilu."
        storyList = loadList('stories')
        userStoryList = {'privateStories': {}, 'publicStories': {}}
        for key, story in storyList.items():
            if story['user'] == userId:
                if not story['public']:
                    if isGranted(userId=userId) or isGranted():
                        userStoryList['privateStories'][key] = story['name']
                else:
                    userStoryList['publicStories'][key] = story['name']

        "Edycja danych użytkownika."
        if request.method == 'POST' and request.form.get('username') and request.form.get('description') is not None and (isGranted(userId=userId) or isGranted()):
            correctUsername = True
            correctDescription = True
            for user in userList:
                if userList[user]['username'] == request.form['username'] and user != userId:
                    flash('Nazwa użytkownika zajęta', 'error')
                    correctUsername = False
                    break
            if len(request.form['username']) < 4 or len(request.form['username']) > 30:
                flash('Nazwa użytkownika musi mieć od 4 do 30 znaków', 'error')
                correctUsername = False
            if len(request.form['description']) > 500:
                flash('Opis profilu musi mieć mniej niż 500 znaków', 'error')
                correctDescription = False
            if correctUsername or correctDescription:
                if correctUsername:
                    userList[userId]['username'] = request.form['username']
                if correctDescription:
                    userList[userId]['description'] = request.form['description']
                saveToDatabase(userId + '.json', {userId: userList[userId]}, 'users')
                flash('Zapisano dane użytkownika')
                if not correctUsername or not correctDescription:
                    flash('Wykryto błędy w formularzu. Nie zapisano wszystkich danych', 'delete')
                userData = dict(userList[userId])
                del userData['password']
            return redirect(url_for('userProfile', userId=userId))

        return render_template('userProfile.html', isAdmin=isGranted(), isProfileOwner=isGranted(userId=userId), userScenarioList=userScenarioList, userStoryList=userStoryList, userData=userData)
    except:
        return redirect(url_for('menu'))


@app.route('/scenarios')
def scenarios():
    "Lista scenariuszy."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        scenarioList = loadList('scenarios')

        "Stworzenie listy scenariuszy do wyświetlenia."
        publicScenarioList = {'privateScenarios': {}, 'publicScenarios': {}, 'publicEditScenarios': {}}
        for key, scenario in scenarioList.items():
            if not scenario['publicView']:
                if isGranted(element=scenario):
                    publicScenarioList['privateScenarios'][key] = scenario['name']
            elif scenario['publicEdit']:
                publicScenarioList['publicEditScenarios'][key] = scenario['name']
            else:
                publicScenarioList['publicScenarios'][key] = scenario['name']

        return render_template('scenarios.html', publicScenarioList=publicScenarioList, isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/start', methods=['GET', 'POST'])
def start():
    "Pytanie startowe scenariusza."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        scenarioId = request.args.get('scenarioId')

        session['scenarioPath'] = []
        session['story'] = []
        session.pop('scenarioData', None)

        "Sprawdzenie poprawności id scenariusza."
        scenarioList = loadList('scenarios')
        if scenarioId:
            if scenarioId in scenarioList:
                if scenarioList[scenarioId]['publicView'] or isGranted(element=scenarioList[scenarioId]):
                    session['scenarioId'] = scenarioId
                    session.pop('questionId', None)
                    return redirect(url_for('start'))
                else:
                    return redirect(url_for('menu'))
            else:
                return redirect(url_for('menu'))
        elif checkScenarioSession(storyRedirect='scenarios'):
            return checkScenarioSession(storyRedirect='scenarios')
        scenario = scenarioList[session['scenarioId']]

        "Sprawdzenie przesłanej odpowiedzi pod kątem słów kluczowych."
        if request.method == 'POST' and request.form.get('startingAnswer'):
            if len(request.form['startingAnswer']) < 1 or len(request.form['startingAnswer']) > 100:
                flash('Odpowiedź na pytanie startowe musi mieć od 1 do 100 znaków', 'error')
                return redirect(url_for('start'))
            if scenario['firstQuestion'] not in scenario['questions']:
                flash('Scenariusz nie posiada ustawionego pierwszego pytania scenariusza', 'error')
                return redirect(url_for('start'))
            foundKeyWord = False
            for keyWord in scenario['keyWords'].values():
                if keyWord.lower() in request.form['startingAnswer'].lower():
                    foundKeyWord = True
                    break
            if not scenario['keyWords'] or foundKeyWord:
                scenarioPath = session['scenarioPath']
                scenarioPath.append(scenario['firstQuestion'])
                session['scenarioPath'] = scenarioPath
                story = session['story']
                story.append({'question': scenario['questions'][scenario['firstQuestion']]['text']})
                session['story'] = story
                session['scenarioData'] = {'scenarioName': scenario['name'], 'owner': scenario['user'], 'startingQuestion': scenario['startingQuestion'], 'startingAnswer': request.form['startingAnswer']}
                return redirect(url_for('question'))
            flash(scenario['noKeyWordsMessage'], 'error')
            return redirect(url_for('start'))

        return render_template('start.html', scenario=scenario, isGranted=isGranted(element=scenario, publicEdit=True), ownerExists=ownerExists(scenario, 'user'), isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/question')
def question():
    "Widok pytania podczas przechodzenia scenariusza."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        if checkScenarioSession(storyRedirect='start'):
            return checkScenarioSession(storyRedirect='start')

        scenario = loadFromDatabase('scenarios', session['scenarioId'] + '.json')[session['scenarioId']]

        questionId = request.args.get('questionId')
        answerId = request.args.get('answerId')

        "Sprawdzenie poprawności przesłanego id pytania."
        if questionId and questionId in scenario['questions'] and answerId and session.get('scenarioPath'):
            if session['scenarioPath'][-1].split("-")[0] in scenario['questions']:
                answers = scenario['questions'][session['scenarioPath'][-1].split("-")[0]]['answers']
                if answerId in answers:
                    answer = answers[answerId]
                    if answer['questionId'] == questionId:
                        if checkRequirements(answer):
                            scenarioPath = session['scenarioPath']
                            scenarioPath.append(questionId)
                            scenarioPath[-2] += "-" + answerId
                            session['scenarioPath'] = scenarioPath
                            story = session['story']
                            story.append({'question': scenario['questions'][questionId]['text']})
                            story[-2]['answer'] = answer['text']
                            session['story'] = story
            return redirect(url_for('question'))

        "Obsługa żadania cofnięcia pytania."
        if request.args.get('goBack') and scenario['goBack'] and session['scenarioPath']:
            scenarioPath = session['scenarioPath']
            scenarioPath.pop()
            story = session['story']
            story.pop()
            if session['scenarioPath']:
                scenarioPath[-1] = scenarioPath[-1].split("-")[0]
                story[-1].pop('answer', None)
            session['scenarioPath'] = scenarioPath
            session['story'] = story
            return redirect(url_for('question'))

        if session.get('scenarioPath') and session['scenarioPath'][-1].split("-")[0] in scenario['questions']:
            currentQuestion = session['scenarioPath'][-1].split("-")[0]
        else:
            return redirect(url_for('start'))

        "Stworzenie listy odpowiedzi do wyświetlenia pod pytaniem."
        answers = dict(scenario['questions'][session['scenarioPath'][-1].split("-")[0]]['answers'])
        for answerId in list(answers):
            if not checkRequirements(answers[answerId]) or answers[answerId]['questionId'] not in scenario['questions']:
                del answers[answerId]

        "Stworzenie listy tekstów opcjonalnych do wyświetlenia pod pytaniem."
        optionalTexts = dict(scenario['questions'][session['scenarioPath'][-1].split("-")[0]]['optionalTexts'])
        for optionalTextId in list(optionalTexts):
            if not checkRequirements(optionalTexts[optionalTextId]):
                del optionalTexts[optionalTextId]

        return render_template('question.html', scenario=scenario, answers=answers, optionalTexts=optionalTexts, questionId=currentQuestion, isGranted=isGranted(element=scenario, publicEdit=True), ownerExists=ownerExists(scenario, 'user'), isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/currentStory', methods=['GET', 'POST'])
def currentStory():
    "Dotychczasowa historia na podstawie przechodzonego scenariusza."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        if not session.get('scenarioPath'):
            return redirect(url_for('menu'))

        storyEnd = False
        "Obsługa żadania zapisania historii."
        if session.get('userId'):
            answers = {}
            scenarioList = loadList('scenarios')
            if session.get('scenarioId') in scenarioList:
                if session['scenarioPath'][-1].split("-")[0] in scenarioList[session['scenarioId']]['questions']:
                    answers = dict(scenarioList[session['scenarioId']]['questions'][session['scenarioPath'][-1].split("-")[0]]['answers'])
                    for answerId in list(answers):
                        if not answers[answerId]['questionId'] or not checkRequirements(answers[answerId]):
                            del answers[answerId]
            if not answers:
                storyEnd = True
                if request.method == 'POST' and request.form.get('name'):
                    storyList = loadList('stories')
                    if len(request.form['name']) < 1 or len(request.form['name']) > 40:
                        flash('Nazwa historii musi mieć od 1 do 40 znaków', 'error')
                        return redirect(url_for('currentStory', saveStory=True))
                    if request.form.get('public'):
                        public = True
                    else:
                        public = False
                    if storyList == {}:
                        key = '0'
                    else:
                        key = str(int(max(storyList, key=int)) + 1)
                    storyList[key] = {'id': key, 'name': request.form.get('name'), 'scenario': session['scenarioId'], 'user': session['userId'], 'owner': session['scenarioData']['owner'], 'scenarioName': session['scenarioData']['scenarioName'], 'public': public, 'startingQuestion': session['scenarioData']['startingQuestion'], 'startingAnswer': session['scenarioData']['startingAnswer'], 'story': session['story']}
                    if storyList[key]['scenario'] not in scenarioList:
                        storyList[key]['scenario'] = ""
                        session.pop('scenarioId', None)
                    userList = loadList('users')
                    if storyList[key]['owner'] not in userList:
                        storyList[key]['owner'] = ""
                    saveToDatabase(key + '.json', {key: storyList[key]}, 'stories')
                    session.pop('scenarioPath', None)
                    session.pop('story', None)
                    session.pop('scenarioData', None)
                    flash('Zapisano historię')
                    return redirect(url_for('userStory', storyId=key))

        return render_template('currentStory.html', storyEnd=storyEnd, isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/userStory', methods=['GET', 'POST'])
def userStory():
    "Widok historii."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        storyId = request.args.get('storyId')
        storyList = loadList('stories')

        if storyId and storyId in storyList:
            story = storyList[storyId]
        else:
            return redirect(url_for('menu'))

        "Sprawdzenie czy zalogowany użytkownik jest właścicielem historii."
        isOwner = False
        if isGranted(userId=story['user']) or isGranted():
            isOwner = True

        if not story['public'] and not isOwner:
            return redirect(url_for('menu'))

        scenarioList = loadList('scenarios')
        scenario = {}
        if story['scenario'] in scenarioList:
            scenario = scenarioList[story['scenario']]

        if isOwner:
            "Usuwanie historii."
            if request.args.get('deleteStory'):
                elementData = {'name': 'story', 'id': storyId, 'storyName': story['name'], 'storyOwner': story['user']}
                return render_template('delete.html', elementData=elementData, isAdmin=isGranted())
            "Potwierdzenie usuwania."
            if request.args.get('confirmDelete'):
                userId = story['user']
                os.remove(PROJECT_ROOT + "/database/stories/" + storyId + ".json")
                flash('Usunięto historię', 'delete')
                return redirect(url_for('userProfile', userId=userId))
            "Edycja danych historii."
            if request.method == 'POST' and request.form.get('name'):
                if len(request.form['name']) < 1 or len(request.form['name']) > 40:
                    flash('Nazwa historii musi mieć od 1 do 40 znaków', 'error')
                    return redirect(url_for('userStory', storyId=storyId))
                story['name'] = request.form['name']
                if request.form.get('public'):
                    story['public'] = True
                else:
                    story['public'] = False
                saveToDatabase(story['id'] + '.json', {story['id']: story}, 'stories')
                flash('Zapisano dane historii')
                return redirect(url_for('userStory', storyId=storyId))

        return render_template('userStory.html', story=story, scenario=scenario, isOwner=isOwner, scenarioOwnerExists=ownerExists(story, 'owner'), storyOwnerExists=ownerExists(story, 'user'), isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/stories')
def stories():
    "Lista historii."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        storyList = loadList('stories')

        "Stworzenie listy historii do wyświetlenia."
        publicStoryList = {'privateStories': {}, 'publicStories': {}}
        for key, story in storyList.items():
            if not story['public']:
                if isGranted(element=story):
                    publicStoryList['privateStories'][key] = story['name']
            else:
                publicStoryList['publicStories'][key] = story['name']

        return render_template('stories.html', publicStoryList=publicStoryList, isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/editScenario', methods=['GET', 'POST'])
def editScenario():
    "Edycja scenariusza."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        if not session.get('userId'):
            return redirect(url_for('menu'))

        scenarioId = request.args.get('scenarioId')
        userId = request.args.get('userId')
        scenarioList = loadList('scenarios')

        "Stworzenie scenariusza."
        if userId:
            if isGranted(userId=userId) or isGranted():
                if scenarioList == {}:
                    key = '0'
                else:
                    key = str(int(max(scenarioList, key=int)) + 1)
                scenarioList[key] = {'id': key, 'name': 'Nowy scenariusz', 'user': userId, 'startingQuestion': 'Pytanie startowe', 'keyWords': {}, 'noKeyWordsMessage': 'Nie znaleziono słów kluczowych. Spróbuj jeszcze raz.', 'firstQuestion': "", 'goBack': True, 'publicView': False, 'publicEdit': False, 'questions': {}}
                saveToDatabase(key + '.json', {key: scenarioList[key]}, 'scenarios')
                flash('Stworzono scenariusz')
                scenarioId = key
            else:
                return redirect(url_for('userProfile'))

        "Sprawdzenie poprawności id scenariusza."
        if scenarioId:
            if scenarioId in scenarioList:
                if isGranted(element=scenarioList[scenarioId], publicEdit=True):
                    session['scenarioId'] = scenarioId
                    session.pop('scenarioPath', None)
                    session.pop('story', None)
                    session.pop('scenarioData', None)
                    session.pop('questionId', None)
                    return redirect(url_for('editScenario'))
                else:
                    return redirect(url_for('menu'))
            else:
                return redirect(url_for('menu'))
        elif checkScenarioSession():
            return checkScenarioSession()
        scenario = scenarioList[session['scenarioId']]

        "Stworzenie słowa kluczowego"
        if request.args.get('createKeyWord'):
            if scenario['keyWords'] == {}:
                key = '0'
            else:
                key = str(int(max(scenario['keyWords'], key=int)) + 1)
            scenario['keyWords'][key] = 'Nowe słowo kluczowe'
            saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')
            flash('Stworzono słowo kluczowe')
            return redirect(url_for('editScenario', _anchor='keyWords'))

        "Usunięcie słowa kluczowego"
        if request.args.get('keyWordId') and request.args.get('keyWordId') in scenario['keyWords']:
            del scenario['keyWords'][request.args.get('keyWordId')]
            saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')
            flash('Usunięto słowo kluczowe', 'delete')
            return redirect(url_for('editScenario', _anchor='keyWords'))

        "Edycja danych scenariusza."
        if request.method == 'POST' and request.form.get('name') and request.form.get('startingQuestion') and request.form.get('noKeyWordsMessage'):
            formError = False
            if len(request.form['name']) < 1 or len(request.form['name']) > 40:
                flash('Nazwa scenariusza musi mieć od 1 do 40 znaków', 'error')
                formError = True
            else:
                scenario['name'] = request.form['name']
            if len(request.form['startingQuestion']) < 1 or len(request.form['startingQuestion']) > 200:
                flash('Pytanie startowe musi mieć od 1 do 200 znaków', 'error')
                formError = True
            else:
                scenario['startingQuestion'] = request.form['startingQuestion']
            if len(request.form['noKeyWordsMessage']) < 1 or len(request.form['noKeyWordsMessage']) > 200:
                flash('Komunikat w przypadku braku słów kluczowych musi mieć od 1 do 200 znaków', 'error')
                formError = True
            else:
                scenario['noKeyWordsMessage'] = request.form['noKeyWordsMessage']
            scenario['firstQuestion'] = request.form.get('firstQuestion')
            if request.form.get('goBack'):
                scenario['goBack'] = True
            else:
                scenario['goBack'] = False
            if isGranted(element=scenario):
                if request.form.get('publicView'):
                    scenario['publicView'] = True
                else:
                    scenario['publicView'] = False
                if request.form.get('publicEdit'):
                    scenario['publicEdit'] = True
                else:
                    scenario['publicEdit'] = False
            keyWordError = False
            for keyWordKey in scenario['keyWords']:
                if len(request.form['keyWord' + keyWordKey]) < 1 or len(request.form['keyWord' + keyWordKey]) > 50:
                    keyWordError = True
                else:
                    scenario['keyWords'][keyWordKey] = request.form['keyWord' + keyWordKey]
            if keyWordError:
                flash('Słowo kluczowe musi mieć od 1 do 50 znaków', 'error')
            saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')
            flash('Zapisano dane scenariusza')
            if formError or keyWordError:
                flash('Wykryto błędy w formularzu. Nie zapisano wszystkich danych', 'delete')
            return redirect(url_for('editScenario'))

        "Dodanie do scenariusza pytań poprzedzających."
        scenario = copy.deepcopy(scenario)
        for scenarioQuestionKey, scenarioQuestion in list(scenario['questions'].items()):
            scenarioQuestion['previousQuestions'] = []
        for scenarioQuestionKey, scenarioQuestion in list(scenario['questions'].items()):
            for answerKey, answer in list(scenarioQuestion['answers'].items()):
                if answer['questionId'] in scenario['questions']:
                    scenario['questions'][answer['questionId']]['previousQuestions'].append(scenarioQuestionKey+'-'+answerKey)
                else:
                    del scenario['questions'][scenarioQuestionKey]['answers'][answerKey]

        return render_template('editScenario.html', scenario=scenario, isGranted=isGranted(element=scenario), ownerExists=ownerExists(scenario, 'user'), isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/deleteScenario')
def deleteScenario():
    "Usuwanie scenariusza."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        scenarioId = request.args.get('scenarioId')
        scenarioList = loadList('scenarios')

        if not scenarioId or scenarioId not in scenarioList or not isGranted(element=scenarioList[scenarioId]):
            return redirect(url_for('menu'))

        scenario = scenarioList[scenarioId]

        "Potwierdzenie usuwania."
        if request.args.get('confirmDelete'):
            "Zmiana danych historii na podstawie usuwanego scenariusza."
            storyList = loadList('stories')
            for storyId in storyList:
                if storyList[storyId]['scenario'] == scenarioId:
                    storyList[storyId]['scenario'] = ''
                    saveToDatabase(storyId + '.json', {storyId: storyList[storyId]}, 'stories')
            userId = scenario['user']
            os.remove(PROJECT_ROOT + "/database/scenarios/" + scenarioId + ".json")
            flash('Usunięto scenariusz', 'delete')
            return redirect(url_for('userProfile', userId=userId))

        elementData = {'name': 'scenario', 'id': scenarioId, 'scenarioName': scenario['name'], 'scenarioOwner': scenario['user']}

        return render_template('delete.html', elementData=elementData, isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/editQuestion', methods=['GET', 'POST'])
def editQuestion():
    "Edycja pytania."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        if checkScenarioSession():
            return checkScenarioSession()

        scenario = loadFromDatabase('scenarios', session['scenarioId'] + '.json')[session['scenarioId']]

        questionId = request.args.get('questionId')

        "Stworzenie pytania."
        if request.args.get('createQuestion'):
            if scenario['questions'] == {}:
                key = '0'
            else:
                key = str(int(max(scenario['questions'], key=int)) + 1)
            scenario['questions'][key] = {'text': 'Nowe pytanie', 'optionalTexts': {}, 'answers': {}}
            saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')
            flash('Stworzono pytanie')
            questionId = key

        "Sprawdzenie poprawności id pytania."
        if questionId:
            if questionId in scenario['questions']:
                session['questionId'] = questionId
                return redirect(url_for('editQuestion'))
            else:
                return redirect(url_for('editScenario'))
        elif not session.get('questionId') or session['questionId'] not in scenario['questions']:
            return redirect(url_for('editScenario'))

        "Stworzenie elementu pytania."
        if request.args.get('element'):
            if request.args.get('element') == 'optionalText':
                createElement('optionalText', {'text': 'Nowy tekst opcjonalny', 'conditionalAnswers': [], 'exclusionAnswers': []}, scenario)
                flash('Stworzono tekst opcjonalny')
                return redirect(url_for('editQuestion', _anchor='optionalText'+str(len(scenario['questions'][session['questionId']]['optionalTexts'])-1)))
            if request.args.get('element') == 'answer':
                createElement('answer', {'text': 'Nowa odpowiedź', 'questionId': '', 'conditionalAnswers': [], 'exclusionAnswers': []}, scenario)
                flash('Stworzono odpowiedź')
                return redirect(url_for('editQuestion', _anchor='answer'+str(len(scenario['questions'][session['questionId']]['answers'])-1)))

        "Stworzenie i usuwanie wymagania elementu pytania."
        if request.args.get('requirement'):
            requirement = request.args.get('requirement').split("-")
            if len(requirement) > 3:
                deleteRequirement(requirement, scenario)
            else:
                createRequirement(requirement, scenario)
            return redirect(url_for('editQuestion', _anchor=requirement[0][:-1]+requirement[2]))

        "Edycja danych pytania."
        if request.method == 'POST' and request.form.get('text'):
            if len(request.form['text']) < 1 or len(request.form['text']) > 200:
                flash('Treść pytania musi mieć od 1 do 200 znaków', 'error')
                questionTextError = True
            else:
                scenario['questions'][session['questionId']]['text'] = request.form['text']
                questionTextError = False
            optionalTextError = False
            for optionalTextKey, optionalText in scenario['questions'][session['questionId']]['optionalTexts'].items():
                if len(request.form['optionalText' + optionalTextKey]) < 1 or len(request.form['optionalText' + optionalTextKey]) > 200:
                    optionalTextError = True
                else:
                    optionalText['text'] = request.form['optionalText' + optionalTextKey]
                for requirementKey in range(len(optionalText['conditionalAnswers'])):
                    optionalText['conditionalAnswers'][requirementKey] = request.form.get('optionalText' + optionalTextKey + 'ConditionalAnswers' + str(requirementKey))
                for requirementKey in range(len(optionalText['exclusionAnswers'])):
                    optionalText['exclusionAnswers'][requirementKey] = request.form.get('optionalText' + optionalTextKey + 'ExclusionAnswers' + str(requirementKey))
            answerError = False
            for answerKey, answer in scenario['questions'][session['questionId']]['answers'].items():
                if len(request.form['answerText' + answerKey]) < 1 or len(request.form['answerText' + answerKey]) > 100:
                    answerError = True
                else:
                    answer['text'] = request.form['answerText' + answerKey]
                answer['questionId'] = request.form['answerQuestionId' + answerKey]
                for requirementKey in range(len(answer['conditionalAnswers'])):
                    answer['conditionalAnswers'][requirementKey] = request.form.get('answer' + answerKey + 'ConditionalAnswers' + str(requirementKey))
                for requirementKey in range(len(answer['exclusionAnswers'])):
                    answer['exclusionAnswers'][requirementKey] = request.form.get('answer' + answerKey + 'ExclusionAnswers' + str(requirementKey))
            if optionalTextError:
                flash('Treść tekstu opcjonalnego musi mieć od 1 do 200 znaków', 'error')
            if answerError:
                flash('Treść odpowiedzi musi mieć od 1 do 100 znaków', 'error')
            saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')
            flash('Zapisano dane pytania')
            if questionTextError or optionalTextError or answerError:
                flash('Wykryto błędy w formularzu. Nie zapisano wszystkich danych', 'delete')
            return redirect(url_for('editQuestion'))

        return render_template('editQuestion.html', scenario=scenario, questionId=session['questionId'], ownerExists=ownerExists(scenario, 'user'), isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/deleteQuestion')
def deleteQuestion():
    "Usuwanie pytania."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        if checkScenarioSession():
            return checkScenarioSession()

        scenario = loadFromDatabase('scenarios', session['scenarioId'] + '.json')[session['scenarioId']]

        questionId = request.args.get('questionId')

        if not questionId or questionId not in scenario['questions']:
            return redirect(url_for('editScenario'))

        "Potwierdzenie usuwania."
        if request.args.get('confirmDelete'):
            del scenario['questions'][questionId]
            if questionId == scenario['firstQuestion']:
                scenario['firstQuestion'] = ""
            saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')
            flash('Usunięto pytanie', 'delete')
            return redirect(url_for('editScenario', _anchor='questions'))

        elementData = {'name': 'question', 'id': questionId, 'questionText': scenario['questions'][questionId]['text']}

        return render_template('delete.html', elementData=elementData, isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


@app.route('/deleteQuestionElement')
def deleteQuestionElement():
    "Usuwanie elementu pytania."
    try:
        if noUserInDatabase():
            return noUserInDatabase()

        if checkScenarioSession():
            return checkScenarioSession()

        scenario = loadFromDatabase('scenarios', session['scenarioId'] + '.json')[session['scenarioId']]

        if not session.get('questionId') or session['questionId'] not in scenario['questions']:
            return redirect(url_for('menu'))

        "Potwierdzenie usuwania."
        if request.args.get('confirmDelete'):
            deleteElement(request.args.get('confirmDelete'), scenario)
            return redirect(url_for('editQuestion'))

        if request.args.get('optionalTextId') and request.args.get('optionalTextId') in scenario['questions'][session['questionId']]['optionalTexts']:
            elementData = {'name': 'optionalText', 'id': request.args.get('optionalTextId'), 'text': scenario['questions'][session['questionId']]['optionalTexts'][request.args.get('optionalTextId')]['text']}
        elif request.args.get('answerId') and request.args.get('answerId') in scenario['questions'][session['questionId']]['answers']:
            elementData = {'name': 'answer', 'id': request.args.get('answerId'), 'text': scenario['questions'][session['questionId']]['answers'][request.args.get('answerId')]['text']}
        else:
            return redirect(url_for('editQuestion'))

        return render_template('delete.html', elementData=elementData, isAdmin=isGranted())
    except:
        return redirect(url_for('menu'))


def createElement(element, pattern, scenario):
    "Funkcja tworząca dany element pytania."
    if scenario['questions'][session['questionId']][element + 's'] == {}:
        key = '0'
    else:
        key = str(int(max(scenario['questions'][session['questionId']][element + 's'], key=int)) + 1)
    scenario['questions'][session['questionId']][element + 's'][key] = pattern
    saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')


def deleteElement(element, scenario):
    "Funkcja usuwająca dany element pytania."
    if element == 'optionalText' or element == 'answer':
        if request.args.get(element + 'Id') and request.args.get(element + 'Id') in scenario['questions'][session['questionId']][element + 's']:
            del scenario['questions'][session['questionId']][element + 's'][request.args.get(element + 'Id')]
            saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')
            if element == 'optionalText':
                flash('Usunięto tekst opcjonalny', 'delete')
            elif element == 'answer':
                flash('Usunięto odpowiedź', 'delete')


def createRequirement(requirement, scenario):
    "Funkcja stwarzająca wymaganie do danego elementu pytania."
    if (requirement[0] == 'optionalTexts' or requirement[0] == 'answers') and (requirement[1] == 'conditionalAnswers' or requirement[1] == 'exclusionAnswers'):
        if requirement[2] in scenario['questions'][session['questionId']][requirement[0]]:
            scenario['questions'][session['questionId']][requirement[0]][requirement[2]][requirement[1]].append("")
            saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')
            if requirement[0] == 'optionalTexts' and requirement[1] == 'conditionalAnswers':
                flash('Stworzono warunek dla tekstu opcjonalnego')
            elif requirement[0] == 'optionalTexts' and requirement[1] == 'exclusionAnswers':
                flash('Stworzono wykluczenie dla tekstu opcjonalnego')
            elif requirement[0] == 'answers' and requirement[1] == 'conditionalAnswers':
                flash('Stworzono warunek dla odpowiedzi')
            elif requirement[0] == 'answers' and requirement[1] == 'exclusionAnswers':
                flash('Stworzono wykluczenie dla odpowiedzi')


def deleteRequirement(requirement, scenario):
    "Funkcja usuwająca wymaganie do danego elementu pytania."
    if (requirement[0] == 'optionalTexts' or requirement[0] == 'answers') and (requirement[1] == 'conditionalAnswers' or requirement[1] == 'exclusionAnswers'):
        if requirement[2] in scenario['questions'][session['questionId']][requirement[0]]:
            if requirement[3].isdigit() and int(requirement[3]) < len(scenario['questions'][session['questionId']][requirement[0]][requirement[2]][requirement[1]]):
                del scenario['questions'][session['questionId']][requirement[0]][requirement[2]][requirement[1]][int(requirement[3])]
                saveToDatabase(session['scenarioId'] + '.json', {session['scenarioId']: scenario}, 'scenarios')
                if requirement[0] == 'optionalTexts' and requirement[1] == 'conditionalAnswers':
                    flash('Usunięto warunek dla tekstu opcjonalnego', 'delete')
                elif requirement[0] == 'optionalTexts' and requirement[1] == 'exclusionAnswers':
                    flash('Usunięto wykluczenie dla tekstu opcjonalnego', 'delete')
                elif requirement[0] == 'answers' and requirement[1] == 'conditionalAnswers':
                    flash('Usunięto warunek dla odpowiedzi', 'delete')
                elif requirement[0] == 'answers' and requirement[1] == 'exclusionAnswers':
                    flash('Usunięto wykluczenie dla odpowiedzi', 'delete')


def checkRequirements(element):
    "Funkcja sprawdzająca wymagania danego elementu pytania."
    condition = True
    noExclusion = True
    if element['conditionalAnswers']:
        condition = False
    if element['exclusionAnswers']:
        noExclusion = False
    if not condition or not noExclusion:
        noExclusion = True
        conditionList = element['conditionalAnswers'].copy()
        for record in session['scenarioPath']:
            if record in element['exclusionAnswers']:
                noExclusion = False
                break
            if not condition and record in conditionList:
                conditionList.remove(record)
                if not conditionList:
                    condition = True
    if condition and noExclusion:
        return True


def noUserInDatabase():
    "Funkcja sprawdzająca czy zalogowany użytkownik znajduje się w bazie."
    userList = loadList('users')
    if session.get('userId') and session['userId'] not in userList:
        return redirect(url_for('logout'))


def checkScenarioSession(storyRedirect=None):
    "Funkcja sprawdzająca poprawność zmiennej sesyjnej przechowującej id scenariusza."
    scenarioList = loadList('scenarios')
    if session.get('scenarioId') and session['scenarioId'] in scenarioList:
        if storyRedirect:
            if not scenarioList[session['scenarioId']]['publicView'] and not isGranted(element=scenarioList[session['scenarioId']]):
                return redirect(url_for(storyRedirect))
        else:
            if not isGranted(element=scenarioList[session['scenarioId']], publicEdit=True):
                return redirect(url_for('menu'))
    elif storyRedirect:
        return redirect(url_for(storyRedirect))
    else:
        return redirect(url_for('menu'))


def ownerExists(element, key):
    "Sprawdzenie czy element posiada właściciela."
    userList = loadList('users')
    if element[key] in userList:
        return True
    else:
        return False


def isGranted(element=None, userId=None, publicEdit=None):
    "Funkcja zwracająca rolę zalogowanego użytkownika."
    if session.get('userId'):
        user = loadFromDatabase('users', session['userId'] + '.json')
        if userId:
            if userId == session['userId']:
                return 'profileOwner'
        else:
            if user[session['userId']]['isAdmin']:
                return 'admin'
            if element:
                if element['user'] == session['userId']:
                    return 'owner'
                if publicEdit:
                    if element['publicView'] and element['publicEdit']:
                        return 'granted'


def loadList(catalog):
    "Funkcja tworząca listę użytkowników, scenariuszy lub historii."
    itemList = {}
    folder = os.listdir(PROJECT_ROOT + "/database/" + catalog + "/")
    folder.sort(key=lambda x: int(x.split(".")[0]))
    for file in folder:
        itemList.update(loadFromDatabase(catalog, file))
    return itemList


def loadFromDatabase(catalog, file):
    "Funkcja wczytująca dane z bazy."
    with open(PROJECT_ROOT + "/database/" + catalog + "/" + file, "r") as read_file:
        targetFile = json.load(read_file)
    return targetFile


def saveToDatabase(name, data, catalog):
    "Funkcja zapisująca dane do bazy."
    with open(PROJECT_ROOT + "/database/" + catalog + "/" + name, "w") as write_file:
        json.dump(data, write_file, indent=4)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5035)
