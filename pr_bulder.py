import re
import time
import argparse
import json
import os
import subprocess
import sys
import requests
import platform
from datetime import datetime
from datetime import timedelta
from artifactory import ArtifactoryPath

from sys import path; \
    path.append("../helper-modules")
import github_util, gocd_util, jenkins_util, jira_util, metrics_util
import branch_merge, gocd_monitor, metadata, migration_rules_update, slack

FUNCTIONS = []
jenkins_pipeline = os.getenv('JENKINS_PIPELINE')
art_user = os.getenv('ART_USER')
art_pass = os.getenv('ART_PASSWORD')
jira_project = os.getenv('JIRA_PROJECT')
jira_url = os.getenv('JIRA')
mono_url = os.getenv('MONO_URL')
mono_git = os.getenv('MONO_GIT')
ms_approved = os.getenv('MILESTONE')
mono_branch = os.getenv('BASE_BRANCH')
mono_pipeline = os.getenv('MONO_PIPELINE')
vm_pipeline = os.getenv('VM_PIPELINE')
aws_pipeline =os.getenv('AWS_PIPELINE')
repo = os.getenv('REPO')
organization = os.getenv('ORGANIZATION')
ova_repo = os.getenv('OVA_REPO')
ap_base_url = os.getenv('AP_BASE_URL')
rb_user = os.getenv('REMOTEBUILD_USER')
rb_token = os.getenv('REMOTEBUILD_TOKEN')
last_step_file = ".last_step.json"
meta_data_file = ".metadata.txt"
logs_path = os.path.join(os.getcwd(), 'logs')
mono_repo = f"{repo}/{organization}"
git_server = github_util.GitHub()
jira_server = jira_util.Jira()
jenkins_server = jenkins_util.Jenkins()

def show_output(question, name, version):
    os.makedirs(logs_path, exist_ok=True)
    timedate = str(datetime.now().replace(microsecond=0))+": "
    print(timedate+f"\033[35mrunning: {question} - \033[4m{name}\033[0m".format(question = question, name = name))
    log_output = timedate + f"running: " + question + " - " + name
    log_file = open(os.path.abspath(logs_path + '/' + version + ".log"), "a")
    print(log_output, file=log_file)
    log_file.close()

def notify(msg):
    ''' notifies after a stage is completed '''
    my_os = platform.system()
    cmd = f"notify-send -u normal '{msg}'" if my_os == 'Linux' else \
        f"osascript -e 'display notification \"{msg}\" with title \"PX notification\"'"
    run(cmd, fatal=False)

def ask(automatic=True, quiet=False):
    ''' gathers function data '''
    def builder(f):
        def wrap(*args, **kargs):
            return f(*args, **kargs)
        assert f.__doc__ is not None, f'missing doc for {f.__name__}'
        assert f.__name__ not in [x['name'] for x in FUNCTIONS]
        assert f.__doc__.strip() not in [x['question'] for x in FUNCTIONS]
        FUNCTIONS.append({
            'question': f.__doc__.strip(),
            'name': f.__name__,
            'func': wrap,
            'quiet': quiet,
            'automatic': automatic
        })
        return wrap
    return builder

def read_state(state_file='.build-state.json'):
    ''' reads json files '''
    return json.loads(open(state_file, 'r').read()) if os.path.exists(state_file) else {}

def save_state(version=None, state=None, st_file=".build-state.json", attempts=0, res=None, step=None):
    """ save the current build state """
    full_state = read_state(state_file=st_file)
    if st_file == ".build-state.json":
        full_state[version] = state
    else:
        full_state.get(step)["attempts"] = attempts
        full_state.get(step)["result"] = res
    with open(st_file, 'w') as fh:
        json.dump(full_state, fh, indent=4, sort_keys=True)

def get_state(version):
    """ load the state for the specified build """
    state = read_state()
    return state[version] if version in state else {}

def get_duration(field1=None, field2=None):
    ''' gets duration between two different stages '''
    start_calc = datetime.strptime(field1, '%Y-%m-%d %H:%M:%S')
    end_calc = datetime.strptime(field2, '%Y-%m-%d %H:%M:%S')
    return (end_calc-start_calc)

def run(cmd, fatal=True):
    ''' run subprocess command '''
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = p.communicate()
    if fatal and p.returncode != 0:
        raise Exception(f"command failed: {cmd}\nSTDOUT: {stdout}\nSTDERR: {stderr}")
    return stdout.decode("utf-8")

def get_value(msg, values=None):
    ''' gets the value the user inputs '''
    while True:
        result = input(msg).strip('\n')
        if not values or result in values:
            break
        else:
            print(f"Please answer with one of these: {', '.join(values)}")
    return result

def get_px(output=True):
    ''' get nested planx repo '''
    if output: print('Grabbing latest repo... May take a few minutes...')
    if os.path.exists(repo):
        os.chdir(repo)
        assert mono_git in run("git remote -v")
        run("git stash")
        run("git clean -fd")
        run("git reset --hard")
        run(f"git checkout {mono_branch}")
        run("git pull")
        return
    run(f"git clone {mono_git}")
    os.chdir(repo)
    run(f"git checkout {mono_branch}")

def should_i(msg):
    ''' asks what stage to continue or start '''
    result = get_value(f'should I {msg}? ', values='yn')
    return True if result[0] == 'y' else False

def get_version(output=True):
    ''' get current version by reading VERSION file '''
    get_px(output=output)
    version = open('VERSION', 'r').read().strip()
    os.chdir('..')
    return version

def get_next_version():
    ''' Increments value of last decimal & ensures last decimal value is 3 digits '''
    version = get_version(output=False)
    values = [int(x) for x in version.split('.')]
    values[-1] = f"{str(values[-1]+1).rjust(3, '0')}"
    return '.'.join([str(x) for x in values])

def get_attempt_num(attempt=1):
    """ gets attempt number for current step """
    state = read_state(state_file=last_step_file)
    if os.path.exists(last_step_file):
        # increments attempt by one if step fails
        attempt = state.get(next(iter(state)))["attempts"] + 1
    return attempt

def check_pr():
    # First check the status of the PR with github
    ready_prs = []
    result = git_server.check_prs(ms_approved)
    if 'errors' in result:
        print("the following PRs are not ready")
        for pr_number in result['errors']:
            git_msg = ""
            pr = git_server.get_pr(pr_number)
            print(f"{pr_number} - {pr.title}")
            for key in result['errors'][pr_number]:
                if key != 'failure' and key != 'labels' and key != 'time':
                    msg = result['errors'][pr_number][key]['message']
                    print(f"    * {key} - {msg}")
                    git_msg += f"{key} - {msg}\n"
            git_server.set_pr_milestone(pr_number, "CAB Requires Changes")
            git_server.make_comment(pr_number, git_msg)
    # Check if ticket exists in pr title then if ticket exists on jira
    if 'ready' in result:
        for pr_number in result['ready']:
            pr = git_server.get_pr(pr_number)
            ticket_check = re.findall(r'^(\w+-\d+)', pr.title, re.IGNORECASE)
            try:
                assert len(ticket_check) <= 1
            except AssertionError:
                print(f"More than one ticket number found in title of PR {pr_number}: {pr.title} -> {ticket_check}", file=sys.stderr)
                git_server.set_pr_milestone(pr_number, "CAB Requires Changes")
                git_server.make_comment(pr_number, f"This PR has multiple ticket numbers \n {ticket_check}")
                continue
            if not ticket_check:
                print(f"The PR {pr_number} is missing a jira ticket in its title: {pr.title}")
                git_server.set_pr_milestone(pr_number, "CAB Requires Changes")
                git_server.make_comment(pr_number, "This PR is missing a jira ticket in its title")
                continue
            else:
                try:
                    for jira_ticket in ticket_check:
                        jira_server.get_issue(jira_ticket.strip())
                    ready_prs.append(pr_number)
                except Exception as e:
                    if "Issue Does Not Exist" in str(e):
                        print(f"The PR {pr_number} is not finding the ticket number associated to it in Jira: {ticket_check}")
                        git_server.set_pr_milestone(pr_number, "CAB Requires Changes")
                        git_server.make_comment(pr_number, f"This PR has a ticket number that doesnt exist in jira \n {ticket_check}")
                    else:
                        print("Jira might be down please check!")
                        slack.main(f"--fail".split())
                        sys.exit(-1)
    return ready_prs

@ask()
def select_prs(version, state):
    "select PRs to include"
    to_add = []
    prs = check_pr()
    for pr_num in prs:
        pr = git_server.get_pr(pr_num)
        msg = f"include this PR -- {pr_num} - {pr.title} --"
        if should_i(msg):
            to_add.append(pr_num)
    if 'manual pr entry' in state:
        to_add += state['manual pr entry']
    assert to_add, 'builds need at least one PR'
    return to_add

@ask()
def make_branch(version, state):
    """ make a new branch """
    get_px(output=False)
    branch = f'{version}-merge'
    run(f'git checkout -b {branch} && git push --set-upstream origin {branch}')
    os.chdir('..')

@ask()
def milestone(version, state):
    """ make a new milestone """
    title = f"{version} CAB Approved"
    try:
        git_server.get_milestone(title)
        print("milestone already exists")
        return
    except Exception as e:
        if 'unable to find milestone' in str(e):
            git_server.create_milestone(title)

@ask()
def add_pr_label(version, state):
    """ adding 'skip-jenkins' label to PRs """
    for pr_num in state['select PRs to include']:
        git_server.add_pr_label(pr_num, 'skip-jenkins')

@ask()
def check_for_schema_tests(version, state):
    """ check for schema_change label to determine if exodus schema comparison tests are needed """
    for pr_num in state['select PRs to include']:
        pull_request = git_server.get_pr(pr_num)
        if "SCHEMA CHANGE" in [label['name'] for label in pull_request.labels]:
            print("Schema Change label detected. Exodus tests will be ran with remotebuild.")
            schema_test_flag = "--EXODUS-TEST"
        else:
            schema_test_flag = ""
        return schema_test_flag

@ask()
def check_for_integration_tests(version, state):
    """ check whether to run integration tests """
    if 'Release' in ms_approved:
        int_flag = "--INTEGRATION-TEST"
    else:
        int_flag  = ""
    return int_flag

@ask()
def move_pr(version, state):
    """ move PRs into new milestone """
    for pr_num in state['select PRs to include']:
        git_server.set_pr_milestone(pr_num, f'{version} CAB Approved')

@ask()
def merge_dev_into_pr(version, state):
    """ merge latest base-branch into each PR """
    while True:
        prs = git_server.get_prs(milestone=f'{version} CAB Approved')
        retry = False
        for pr in prs:
            pr = git_server.get_pr(pr.number)
            merge_state, pr_num = pr.mergeable_state, pr.number
            if merge_state == 'behind' or merge_state == 'unknown':
                git_server.update_branch(pr_num) if merge_state == 'behind' else \
                    print(f"waiting for github to determine merge state for {pr_num}")
                retry = True
            else:
                msg = f'PR Merge is currently: {merge_state}'
                assert merge_state in ['clean', 'blocked', 'unstable', 'has_hooks'], msg
        if not retry:
            break

@ask()
def meta_pr(version, state):
    """ create meta PR """
    # Create the meta PR before branch-merge to ensure Jenkins testing includes these files
    branch = f'{version}-merge'
    meta_branch = metadata.main(f'--commit --current-release {version}'.split()).strip()
    new_pr = git_server.new_pr(f"{version} metadata", meta_branch, branch)
    git_server.add_pr_label(new_pr.number, 'skip-jenkins')
    git_server.set_pr_milestone(new_pr.number, f'{version} CAB Approved')
    os.chdir('../')

@ask()
def branch_merge_pr(version, state):
    """ run branch-merge """
    branch = branch_merge.main(["--log", "--push", "-m", f"{version} CAB Approved"])
    os.chdir('../')
    return branch.strip()

@ask()
def remotebuild(version, state):
    """ run remotebuild """
    last = read_state(state_file=last_step_file)
    start = last.get(next(iter(last)))['time']
    branch = state['run branch-merge']['result']
    int_flag = state['check whether to run integration tests']['result']
    schema_test_flag = state['check for schema_change label to determine if exodus schema comparison tests are needed']['result']
    # This kicks off the ike-build pipeline with the specified parameters
    run(f"remotebuild --branch {branch} --component cluster --step all --VM-TEST --UNIT-TEST {schema_test_flag} {int_flag} --jenkins_agent build_controller --jenkins_job {jenkins_pipeline}")
    time.sleep(30)
    output = jenkins_server.monitor(branch)
    for key in output.keys():
        res = {'url': key, 'status': output.get(key)['status'], 'stage': output.get(key)['stage'], \
            'build_num': list(filter(None, key.split("/")))[-1]}
    assert res['build_num'], f'no build number for build controller job {branch}'
    assert res['status'], f'Build Failed or was Aborted!'
    return {"build_info": res, "duration": (get_duration(field1=start, field2=str(datetime.now().replace(microsecond=0))).total_seconds())/60.0 }

@ask()
def get_jenkins_artifacts(version, state):
    ''' pull jenkins build artifacts '''
    run("mkdir artifacts")
    files = ["docker_stats.json", "allure-report.zip", "build_ike_verbose.log", "artifacts/local_migration_new.json"]
    for file_path in files:
        if os.path.exists(file_path): os.remove(file_path)
    jenkins_server.get_artifact(int(state['run remotebuild']['result']['build_info']['build_num']), files)
    run("mv artifacts/local_migration_new.json . && rm -rf artifacts")

@ask()
def update_base(version, state):
    """ update base branch of PRs """
    prs = git_server.get_prs(milestone=f'{version} CAB Approved')
    for pr in prs:
        print(f"\t updating: {pr.number}")
        git_server.set_pr_base(pr.number, f'{version}-merge')

@ask()
def new_jira_version(version, state):
    """ create a new version in jira """
    tickets = git_server.jira(f'{version} CAB Approved', version, jira_project)
    projects = jira_project.split()
    for project in projects:
        if project in tickets:
            print("ticket contains project")
            jira_server.new_version(version, project)


@ask()
def update_tickets(version, state):
    """ update jira tickets for PRs """
    tickets = git_server.jira(f'{version} CAB Approved', version, jira_project)
    for ticket in json.loads(tickets):
        jira_server.set_fix_version(ticket, version)

@ask()
def merge_prs(version, state):
    """ merge PRs for milestone """
    branch = f'{version}-merge'
    prs = git_server.get_prs(milestone=f'{version} CAB Approved')
    for pr in prs:
        pr = git_server.get_pr(pr.number)
        assert pr.base.label == f'planx:{branch}', f"PR does not have the right target: {pr.number} - {pr.base.label}"
        pr = git_server.get_pr(pr.number)
        if not pr.merged:
            git_server.merge(pr.number)
            result = git_server.get_prs(milestone=f'{version} CAB Approved')
            open("/tmp/wtf.out", "w").write(str(result))
            time.sleep(5)

@ask()
def sql_migration_json(version, state):
    ''' update local migration json '''
    migration_rules_update.main(f'--commit --current-release {version} --migration --code-release'.split())
    os.chdir('../')

@ask()
def exodus_rules(version, state):
    ''' update exodus rules '''
    migration_rules_update.main(f'--commit --current-release {version} --code-release'.split())
    os.chdir('../')

@ask()
def final_pr(version, state):
    """ create & merge PR for the next release """
    branch = f'{version}-merge'
    new_pr = git_server.new_pr(f"{version} merge", branch, mono_branch)
    git_server.add_pr_label(new_pr.number, 'skip-jenkins')
    git_server.set_pr_milestone(new_pr.number, f"{version} CAB Approved")
    time.sleep(30)
    git_server.merge(new_pr.number)
    return new_pr.number

@ask()
def close_milestone(version, state):
    """ close milestone and milestone count"""
    git_server.close_milestone(f'{version} CAB Approved')

@ask()
def remove_pr_label(version, state):
    """ removing 'skip-jenkins' label to PRs """
    for pr in state['select PRs to include']:
        git_server.rm_pr_label(pr, 'skip-jenkins')

@ask()
def delete_branches(version, state):
    """ delete branches in closed milestone """
    # delete branches in milestone and temp branch
    git_server.prune_milestone(f'{version} CAB Approved')
    git_server.delete_branch(state['run branch-merge']['result'])

@ask()
def delete_oldest_milestone(version, state):
    ''' delete oldest closed milestone '''
    git_server.delete_n_oldest_milestones(1)

@ask()
def set_major_version_milestone(version, state):
    """ add major version milestone to PR """
    try:
        for pr_num in state['select PRs to include']:
            git_server.set_pr_milestone(pr_num, f'{version}'[:4])
    except Exception as e:
        if 'unable to find milestone' in str(e):
            print("Major Version milestone needs to be created")

@ask()
def add_patch_label(version, state):
    """ adding 'patch' label to PRs """
    if 'Release' in ms_approved:
       for pr_num in state['select PRs to include']:
           git_server.add_pr_label(pr_num, 'PATCH')

@ask()
def get_ova_details(version, state):
    """ get ova details """
    pipe_ver = state['run remotebuild']['result']["build_info"]["build_num"]
    ova_storage_api = \
        f'{ap_base_url}/api/storage/{ova_repo}/{pipe_ver}/ikeBox-{vm_pipeline}-{pipe_ver}.ova'
    ova_link = ova_storage_api.replace("api/storage/", "")
    jsonData = requests.get(ova_storage_api)
    jsonData = json.loads(jsonData.text)
    ova_size = float(jsonData['size']) / float(1000000000)
    print(f'\t OVA size: {str(ova_size)} GB')
    return {"ova_size": str(ova_size), "ova_link": ova_link}

@ask()
def upload_to_artifactory(version, state):
    """ upload items to artifactory """
    artifacts = ['allure-report.zip', 'build_ike_verbose.log']
    art_folder = state['run remotebuild']['result']["build_info"]["build_num"]
    art_path = ArtifactoryPath(f'{ap_base_url}/{ova_repo}/{vm_pipeline}/{art_folder}', auth=(f'{art_user}', f'{art_pass}'))
    for i in artifacts:
        art_path.deploy_file(i)

@ask()
def release(version, state):
    """ make a release on github """
    pr_info = ""
    for pr in state["select PRs to include"]:
        pr_data = git_server.get_pr(pr)
        pr_title = (str(re.sub(r'[^\x00-\x7F]+',' ', pr_data.title)))
        owner = git_server.get_user_real_name(pr_data.user.login)
        pr_info += "\n".join([pr_title,f"Owner: {owner.strip()}", f"{pr_data.html_url}\n\n"])
    data = f'{pr_info}OVA: {state["get ova details"]["result"]["ova_link"]}'
    open(meta_data_file, "w").write(data)
    git_server.create_dev_release(version, data, mono_branch)

@ask()
def pr_queue(version, state):
    """ count pr queue """
    time.sleep(5 * 60)
    try:
        check_pr()
    except:
        pass
    pr_count = len(git_server.get_prs(milestone=ms_approved))
    pr_list = git_server.check_prs(ms_approved, fatal=False)
    pr_list = [x for x in pr_list['ready']] if pr_list else None
    pr_list = [ git_server.get_pr(item).title for item in pr_list ] if pr_list else None
    return {"pr_count": pr_count, "pr_list": pr_list}

@ask()
def calculate_metrics(version, state):
    """ calculate reported metrics """
    jenkins_duration = float(state['run remotebuild']['result']['duration'])
    ova_size = state['get ova details']["result"]["ova_size"]
    attempts = {
        "remotebuild_attempts": state['run remotebuild']["attempts"]
    }
    pr_queue = state['count pr queue']['result']['pr_count']
    pr_labels = git_server.get_pr_labels(state['create & merge PR for the next release']['result'])
    pr_labels = str([ label.name for label in pr_labels ]).replace(", '", ",'").strip()
    total_duration = jenkins_duration 
    milestone = git_server.get_milestone(f"{version} CAB Approved", state='closed')
    metrics = metrics_util.Elk(version, milestone)
    metrics.commit_dev_stats(jenkins_duration, total_duration, attempts, ova_size, pr_labels, pr_queue)
    return str(timedelta(minutes=total_duration))

@ask()
def slack_message(version, state):
    """ slack message """
    slack.main(f'--version {version}'.split())

def main(raw_args=None):
    """ run the PX build process """
    def arguments():
        parser = argparse.ArgumentParser(usage="build PX")
        parser.add_argument('include', type=int, nargs='*')
        parser.add_argument('--onlynew', action='store_true', default=False)
        parser.add_argument("--auto", action='store_true', default=False)
        parser.add_argument("--failed", action='store_true', default=False)
        return parser.parse_args(raw_args)

    args = arguments()
    version = get_version()

    while True:
        state = get_state(version)
        if args.failed:
            print('Kicking PR out of CAB...')
            current = read_state()

            failed = list(current.items())
            failed_version = failed[-1][0]

            # if args.fails, ask to kick pr out of queue
            if should_i(f'Kick {failed_version} out of queue '):
                print(f'Kicking {failed_version} out of CAB...')
                milestone = os.path.join(failed_version + " CAB Approved")
                print(f'milestone: {milestone}')

                # get all prs in milestone
                result = git_server.get_prs(milestone)
                for pr in result:
                    # if user is build-controller, delete pr and close PR
                    if str(pr.user) == "build-controller":
                        branch = git_server.get_branch(pr.number)
                        print(f"deleting this branch: {branch}")
                        git_server.close_pull_request(pr.number)
                        git_server.delete_branch(branch)
                    else:
                        branch = git_server.get_branch(pr.number)
                        print(f"This is the PR number that is getting kicked out of queue: {pr.number}")
                        pr_link = os.path.join('https://github-enterprise.px.ftw/planx/planx/pull/' + str(pr.number))
                        git_server.set_pr_milestone(pr.number, "CAB Requires Changes")
                        git_server.rm_pr_label(pr.number, 'skip-jenkins')
                        print(f'Here is a link to the PR: {pr_link}')

                # closing milestone
                print(f"Closing milestone {milestone}")
                git_server.close_milestone(milestone)

                # get and close temp branch created by bc
                bc_temp_branch = current[failed_version]['run branch-merge']['result']
                print(f"bc temp branch that will be deleted: {bc_temp_branch}")
                git_server.delete_branch(bc_temp_branch)
                break
            else:
                raise Exception("nothing to do")
        elif 'done' in state:
            version = get_next_version()
            continue
        elif not state:
            if args.onlynew or should_i(f"build {version}"):
                break
            version = get_value("What should I use? ")
            continue
        else:
            if args.onlynew:
                raise Exception(f"previous build did not finish {version}")
            if should_i(f"continue building {version}"):
                break
            if not should_i("make a new build"):
                raise Exception("nothing to do")
            else:
                version = get_value("What should I use? ")
                continue

    if 'manual pr entry' not in state: state['manual pr entry'] = args.include

    if args.auto:
        assert args.include, "PRs must be specified"
        state['select PRs to include'] = args.include
    try:
        for func in FUNCTIONS:
            if func['question'] not in state:
                if func['automatic']:
                    show_output(func['question'], func['name'], version)
                    attempt = get_attempt_num()
                    if os.path.exists(last_step_file):
                        # if current step is different than whats in last_step file reset attempt back to 1
                        attempt = 1 if next(iter(read_state(state_file=last_step_file))) != func['question'] else attempt
                        last_step = read_state(state_file=last_step_file)
                    timestamp = str(datetime.now().replace(microsecond=0)) if attempt <= 1 else last_step.get(next(iter(last_step)))['time']
                    with open(last_step_file, 'w') as last_step:
                        json.dump({func['question']: {"attempts": attempt, "time": timestamp,"result": None}}, last_step, indent=4, sort_keys=True)
                    result = func['func'](version, state)

                elif should_i(func['question']): result = func['func'](version, state)

                save_state(st_file=last_step_file, attempts=attempt, res=result, step=func['question'])
                state[func['question']] = read_state(state_file=last_step_file)[func['question']]

                # if the current step is the below state we skip the extra metadata details
                if func['question'] == 'select PRs to include': state[func['question']] = result

                save_state(version=version, state=state)
        state['done'] = True
    finally:
        save_state(version=version, state=state)

if __name__ == '__main__':
    main()

