import platform
import argparse
import time
import json
import re
import os
import shutil
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from prompts import SYSTEM_PROMPT, SYSTEM_PROMPT_TEXT_ONLY
from openai import OpenAI, AzureOpenAI
from utils import get_web_element_rect, encode_image, extract_information, print_message, print_message_complete,\
    get_webarena_accessibility_tree, get_pdf_retrieval_ans_from_assistant, clip_message_and_obs, clip_message_and_obs_text_only

from crawler_crawl4ai import crawler, crawler_custom
from utils import get_webtext_help_from_assistant, truncate_input, get_observer_help_from_assistant


def setup_logger(folder_path):
    log_file_path = os.path.join(folder_path, 'agent.log')

    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    handler = logging.FileHandler(log_file_path, encoding='utf-8')
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def driver_config(args):
    options = webdriver.ChromeOptions()
    # options.add_argument("user-data-dir=D:\WebVoyager\selenium")

    if args.save_accessibility_tree:
        args.force_device_scale = True

    if args.force_device_scale:
        options.add_argument("--force-device-scale-factor=1")
    if args.headless:
        options.add_argument("--headless")
        # https://github.com/SeleniumHQ/selenium/issues/14544
        # options.add_argument("--headless=old")
        # options.add_argument( "--remote-debugging-pipe" )

        options.add_argument(
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
    options.add_experimental_option(
        "prefs", {
            "download.default_directory": args.download_dir,
            "plugins.always_open_pdf_externally": True
        }
    )
    
    options.add_argument("disable-blink-features=AutomationControlled")
    return options


def format_msg(it, init_msg, pdf_obs, other_file_obs, warn_obs, web_img_b64, current_visible_range, web_text, web_text_assist):
    web_text_assist = 'web assistant:'+web_text_assist if web_text_assist else ''
    if it == 1:
        init_msg += f"Observation: {web_text_assist} I've provided the tag name of each element and the text it contains (if text exists). Note that <textarea> or <input> may be textbox, but not exactly. Please focus more on the screenshot and then refer to the textual information.\n{web_text}"
        init_msg_format = {
            'role': 'user',
            'content': [
                {'type': 'text', 'text': init_msg},
            ]
        }
        init_msg_format['content'].append({"type": "image_url",
                                           "image_url": {"url": f"data:image/png;base64,{web_img_b64}"}})
        return init_msg_format
    else:
        if pdf_obs:
            curr_msg = {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': f"Observation: {pdf_obs} Please analyze the response given by Assistant, then consider whether to continue iterating or not. The screenshot of the current page is also attached, give the Thought and Action. I've provided the tag name of each element and the text it contains (if text exists). Note that <textarea> or <input> may be textbox, but not exactly. Please focus more on the screenshot and then refer to the textual information.\n{web_text}"},
                    {
                        'type': 'image_url',
                        'image_url': {"url": f"data:image/png;base64,{web_img_b64}"}
                    }
                ]
            }

        elif other_file_obs:
            curr_msg = {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': f"Observation: {other_file_obs} Please analyze the response given by Assistant, then consider whether to continue iterating or not. The screenshot of the current page is also attached, give the Thought and Action. I've provided the tag name of each element and the text it contains (if text exists). Note that <textarea> or <input> may be textbox, but not exactly. Please focus more on the screenshot and then refer to the textual information.\n{web_text}"},
                    {
                        'type': 'image_url',
                        'image_url': {"url": f"data:image/png;base64,{web_img_b64}"}
                    }
                ]
            }
        
        else: # no any file download
            curr_msg = {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': f"Observation:{warn_obs} {web_text_assist} please analyze the attached screenshot ({current_visible_range}) and give the Thought and Action. I've provided the tag name of each element and the text it contains (if text exists). Note that <textarea> or <input> may be textbox, but not exactly. Please focus more on the screenshot and then refer to the textual information.\n{web_text}"},
                    {
                        'type': 'image_url',
                        'image_url': {"url": f"data:image/png;base64,{web_img_b64}"}
                    }
                ]
            }
            
        return curr_msg


def format_msg_text_only(it, init_msg, pdf_obs, other_file_obs, warn_obs, ac_tree):
    if it == 1:
        init_msg_format = {
            'role': 'user',
            'content': init_msg + '\n' + ac_tree
        }
        return init_msg_format
    else:
        if pdf_obs:
            curr_msg = {
                'role': 'user',
                'content': f"Observation: {pdf_obs} Please analyze the response given by Assistant, then consider whether to continue iterating or not. The accessibility tree of the current page is also given, give the Thought and Action.\n{ac_tree}"
            }

        elif other_file_obs:
            curr_msg = {
                'role': 'user',
                'content': f"Observation: {other_file_obs} Please analyze the response given by Assistant, then consider whether to continue iterating or not. The accessibility tree of the current page is also given, give the Thought and Action.\n{ac_tree}"
            }

        else:
            curr_msg = {
                'role': 'user',
                'content': f"Observation:{warn_obs} please analyze the accessibility tree and give the Thought and Action.\n{ac_tree}"
            }
            
        return curr_msg


def call_gpt4v_api(args, openai_client, messages):
    retry_times = 0
    while True:
        try:
            if not args.text_only:
                logging.info('Calling gpt4v API...')
                if args.api_model.startswith('o'): # reasoning model
                    openai_response = openai_client.chat.completions.create(
                        model=args.api_model, messages=messages, reasoning_effort="low", max_completion_tokens=25000, seed=args.seed
                    )
                else: # normal model
                    openai_response = openai_client.chat.completions.create(
                        model=args.api_model, messages=messages, max_tokens=1000, seed=args.seed
                    )
            else:
                logging.info('Calling gpt4 API...')
                openai_response = openai_client.chat.completions.create(
                    model=args.api_model, messages=messages, max_tokens=1000, seed=args.seed, timeout=30
                )

            prompt_tokens = openai_response.usage.prompt_tokens
            completion_tokens = openai_response.usage.completion_tokens

            logging.info(f'Prompt Tokens: {prompt_tokens}; Completion Tokens: {completion_tokens}')

            gpt_call_error = False
            return prompt_tokens, completion_tokens, gpt_call_error, openai_response

        except Exception as e:
            logging.info(f'Error occurred, retrying. Error type: {type(e).__name__}')

            if type(e).__name__ == 'RateLimitError':
                time.sleep(10)

            elif type(e).__name__ == 'APIError':
                time.sleep(15)

            elif type(e).__name__ == 'InvalidRequestError':
                gpt_call_error = True
                return None, None, gpt_call_error, None

            else:
                gpt_call_error = True
                return None, None, gpt_call_error, None

        retry_times += 1
        if retry_times == 10:
            logging.info('Retrying too many times')
            return None, None, True, None


def exec_action_goback(task_url, driver_task) -> bool:
    # history_length = driver_task.execute_script("return window.history.length;")
    # if history_length <3:
    #     return

    if driver_task.current_url != task_url:
        driver_task.back()
        # driver_task.execute_script("window.history.go(-1)")
        time.sleep(2)
        return True
    return False


def exec_action_click(info, web_ele, driver_task):
    driver_task.execute_script("arguments[0].setAttribute('target', '_self')", web_ele)
    web_ele.click()
    time.sleep(3)


def exec_action_type(info, web_ele, driver_task):
    warn_obs = ""
    type_content = info['content']

    # remove " from start and end of the string
    type_content = type_content.strip('"')

    ele_tag_name = web_ele.tag_name.lower()
    ele_type = web_ele.get_attribute("type")
    # outer_html = web_ele.get_attribute("outerHTML")
    if (ele_tag_name != 'input' and ele_tag_name != 'textarea') or (ele_tag_name == 'input' and ele_type not in ['text', 'search', 'password', 'email', 'tel']):
        warn_obs = f"note: The web element you're trying to type may not be a textbox, and its tag name is <{web_ele.tag_name}>, type is {ele_type}."
    try:
        # Not always work to delete
        web_ele.clear()
        # Another way to delete
        if platform.system() == 'Darwin':
            web_ele.send_keys(Keys.COMMAND + "a")
        else:
            web_ele.send_keys(Keys.CONTROL + "a")
        web_ele.send_keys(" ")
        web_ele.send_keys(Keys.BACKSPACE)
    except:
        pass

    actions = ActionChains(driver_task)
    actions.click(web_ele).perform()
    actions.pause(1)

    try:
        driver_task.execute_script("""window.onkeydown = function(e) {if(e.keyCode == 32 && e.target.type != 'text' && e.target.type != 'textarea' && e.target.type != 'search') {e.preventDefault();}};""")
    except:
        pass

    actions.send_keys(type_content)
    actions.pause(2)

    actions.send_keys(Keys.ENTER)
    actions.perform()
    time.sleep(10)
    return warn_obs


def exec_action_scroll(info, web_eles, driver_task, args, obs_info):
    scroll_ele_number = info['number']
    scroll_content = info['content']
    if scroll_ele_number == "WINDOW":
        if scroll_content == 'down':
            driver_task.execute_script(f"window.scrollBy(0, {args.window_height*2//3});")
        else:
            driver_task.execute_script(f"window.scrollBy(0, {-args.window_height*2//3});")
    else:
        if not args.text_only:
            scroll_ele_number = int(scroll_ele_number)
            web_ele = web_eles[scroll_ele_number]
        else:
            element_box = obs_info[scroll_ele_number]['union_bound']
            element_box_center = (element_box[0] + element_box[2] // 2, element_box[1] + element_box[3] // 2)
            web_ele = driver_task.execute_script("return document.elementFromPoint(arguments[0], arguments[1]);", element_box_center[0], element_box_center[1])
        actions = ActionChains(driver_task)
        driver_task.execute_script("arguments[0].focus();", web_ele)
        if scroll_content == 'down':
            actions.key_down(Keys.ALT).send_keys(Keys.ARROW_DOWN).key_up(Keys.ALT).perform()
        else:
            actions.key_down(Keys.ALT).send_keys(Keys.ARROW_UP).key_up(Keys.ALT).perform()
    time.sleep(3)


def exec_action_scroll_dynamic_load(driver_task, args, move_amount=4):
    current_scroll_position = driver_task.execute_script("return window.pageYOffset;")
    for _ in range(move_amount):
        driver_task.execute_script(f"window.scrollBy(0, {args.window_height*3});")    
        time.sleep(0.25)
    driver_task.execute_script(f"window.scrollTo(0, {current_scroll_position});")

def execute_task(args, client, options, result_dir, task):
    task_dir = os.path.join(result_dir, 'task{}'.format(task["id"]))
    os.makedirs(task_dir, exist_ok=True)
    if args.web_markdown:
        os.makedirs(os.path.join(task_dir,'web_dump'), exist_ok=True)
        if args.web_assistant:
            os.makedirs(os.path.join(task_dir,'web_assistant'), exist_ok=True)
    setup_logger(task_dir)
    logging.info(f'########## TASK{task["id"]} ##########')

    driver_task = webdriver.Chrome(options=options)

    # About window size, 765 tokens
    # You can resize to height = 512 by yourself (255 tokens, Maybe bad performance)
    driver_task.set_window_size(args.window_width, args.window_height)  # larger height may contain more web information
    driver_task.get(task['web'])
    task['web'] = driver_task.current_url
    try:
        driver_task.find_element(By.TAG_NAME, 'body').click()
        # 檢查跳轉
        if driver_task.current_url != task['web']:
            print("Unexpected navigation occurred!")
            # 如果有跳轉，可以嘗試返回或其他處理
            driver_task.back()
    except:
        pass
    # sometimes enter SPACE, the page will sroll down
    driver_task.execute_script("""window.onkeydown = function(e) {if(e.keyCode == 32 && e.target.type != 'text' && e.target.type != 'textarea') {e.preventDefault();}};""")
    time.sleep(5)

    # We only deal with PDF file
    for filename in os.listdir(args.download_dir):
        file_path = os.path.join(args.download_dir, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    download_files = []  # sorted(os.listdir(args.download_dir))
    url_history = [task['web']]

    fail_obs = ""  # When error execute the action
    pdf_obs = ""  # When download PDF file
    other_download_obs = ""  # When download other file
    warn_obs = ""  # Type warning
    pattern = r'Thought:|Action:|Observation:'

    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    obs_prompt = "Observation: please analyze the attached screenshot and give the Thought and Action. "
    if args.text_only:
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT_TEXT_ONLY}]
        obs_prompt = "Observation: please analyze the accessibility tree and give the Thought and Action."

    init_msg = f"""Now given a task: {task['ques']}  Please interact with https://www.example.com and get the answer. \n"""
    init_msg = init_msg.replace('https://www.example.com', task['web'])
    init_msg = init_msg + obs_prompt

    it = 0
    accumulate_prompt_token = 0
    accumulate_completion_token = 0


    while it < args.max_iter:
        logging.info(f'Iter: {it}')
        it += 1
        if not fail_obs:
            if args.dynamic_load:
                exec_action_scroll_dynamic_load(driver_task, args)
            
            if args.web_markdown:
                b64_img_clean = driver_task.get_screenshot_as_base64()
                crawler_text = crawler_custom(driver_task.current_url, driver_task.page_source, b64_img_clean)
                crawler_text = truncate_input(crawler_text, max_tokens=126000)
                with open(os.path.join(task_dir, 'web_dump', 'web_dump{}.md'.format(it)), 'w', encoding='utf-8') as f:
                    f.write(crawler_text)

                web_text_assist = crawler_text # if web assistant not used, use markdown only
                if args.web_assistant:
                    web_text_assist = get_webtext_help_from_assistant(client, crawler_text, task['ques'])
                    with open(os.path.join(task_dir, 'web_assistant', 'web_assistant{}.md'.format(it)), 'w', encoding='utf-8') as f:
                        f.write(web_text_assist)
            else:
                web_text_assist = ''

            if driver_task.current_url != url_history[-1]:
                url_history.append(driver_task.current_url)

            try:
                if not args.text_only:
                    rects, web_eles, web_eles_text = get_web_element_rect(driver_task, fix_color=args.fix_box_color)
                else:
                    accessibility_tree_path = os.path.join(task_dir, 'accessibility_tree{}'.format(it))
                    ac_tree, obs_info = get_webarena_accessibility_tree(driver_task, accessibility_tree_path)

            except Exception as e:
                if not args.text_only:
                    logging.error('Driver error when adding set-of-mark.')
                else:
                    logging.error('Driver error when obtaining accessibility tree.')
                logging.error(e)
                break

            img_path = os.path.join(task_dir, 'screenshot{}.png'.format(it))
            driver_task.save_screenshot(img_path)

            current_visible_range = driver_task.execute_script('const scrollTop = window.scrollY; const scrollHeight = document.documentElement.scrollHeight - window.innerHeight; const startPercentage = (scrollTop / scrollHeight) * 100;  const endPercentage = ((scrollTop + window.innerHeight) / scrollHeight) * 100; return `Currently visible range：${startPercentage.toFixed(2)}% - ${endPercentage.toFixed(2)}%`;')

            # accessibility tree
            if (not args.text_only) and args.save_accessibility_tree:
                accessibility_tree_path = os.path.join(task_dir, 'accessibility_tree{}'.format(it))
                get_webarena_accessibility_tree(driver_task, accessibility_tree_path)

            # encode image
            b64_img = encode_image(img_path)

            # format msg
            if not args.text_only:
                curr_msg = format_msg(it, init_msg, pdf_obs, other_download_obs, warn_obs, b64_img, current_visible_range, web_eles_text, web_text_assist)
            else:
                curr_msg = format_msg_text_only(it, init_msg, pdf_obs, other_download_obs, warn_obs, ac_tree)
            messages.append(curr_msg)
        else:
            curr_msg = {
                'role': 'user',
                'content': fail_obs
            }
            messages.append(curr_msg)

        # Clip messages, too many attached images may cause confusion
        if not args.text_only:
            clip_messages = clip_message_and_obs(messages, args.max_attached_imgs)
        else:
            clip_messages = clip_message_and_obs_text_only(messages, args.max_attached_imgs)

        # Call GPT-4v API
        prompt_tokens, completion_tokens, gpt_call_error, openai_response = call_gpt4v_api(args, client, clip_messages)

        if gpt_call_error:
            break
        else:
            accumulate_prompt_token += prompt_tokens
            accumulate_completion_token += completion_tokens
            logging.info(f'Accumulate Prompt Tokens: {accumulate_prompt_token}; Accumulate Completion Tokens: {accumulate_completion_token}')
            logging.info('API call complete...')
        gpt_4v_res = openai_response.choices[0].message.content
        messages.append({'role': 'assistant', 'content': gpt_4v_res})


        # remove the rects on the website
        if (not args.text_only) and rects:
            logging.info(f"Num of interactive elements: {len(rects)}")
            for rect_ele in rects:
                driver_task.execute_script("arguments[0].remove()", rect_ele)
            rects = []
            # driver_task.save_screenshot(os.path.join(task_dir, 'screenshot{}_no_box.png'.format(it)))


        # extract action info
        try:
            assert 'Thought:' in gpt_4v_res and 'Action:' in gpt_4v_res
        except AssertionError as e:
            logging.error(e)
            fail_obs = "Format ERROR: Both 'Thought' and 'Action' should be included in your reply."
            continue

        # bot_thought = re.split(pattern, gpt_4v_res)[1].strip()
        chosen_action = re.split(pattern, gpt_4v_res)[2].strip()
        # print(chosen_action)
        action_key, info = extract_information(chosen_action)

        fail_obs = ""
        pdf_obs = ""
        other_download_obs = ""
        warn_obs = ""
        # execute action
        try:
            window_handle_task = driver_task.current_window_handle
            driver_task.switch_to.window(window_handle_task)

            if action_key == 'click':
                if not args.text_only:
                    click_ele_number = int(info[0])
                    web_ele = web_eles[click_ele_number]
                else:
                    click_ele_number = info[0]
                    element_box = obs_info[click_ele_number]['union_bound']
                    element_box_center = (element_box[0] + element_box[2] // 2,
                                            element_box[1] + element_box[3] // 2)
                    web_ele = driver_task.execute_script("return document.elementFromPoint(arguments[0], arguments[1]);", element_box_center[0], element_box_center[1])

                ele_tag_name = web_ele.tag_name.lower()
                ele_type = web_ele.get_attribute("type")

                exec_action_click(info, web_ele, driver_task)

                # deal with PDF file
                current_files = sorted(os.listdir(args.download_dir))
                if current_files != download_files:
                    # wait for download finish
                    time.sleep(10)
                    current_files = sorted(os.listdir(args.download_dir))

                    current_download_file = [pdf_file for pdf_file in current_files if pdf_file not in download_files]
                    current_download_pdf_file = [file for file in current_files if file.endswith('.pdf')]
                    if current_download_file:
                        if current_download_pdf_file:
                            pdf_file = current_download_pdf_file[0]
                            pdf_obs = get_pdf_retrieval_ans_from_assistant(client, os.path.join(args.download_dir, pdf_file), task['ques'])
                            shutil.copy(os.path.join(args.download_dir, pdf_file), task_dir)
                            pdf_obs = "You downloaded a PDF file, I ask the Assistant API to answer the task based on the PDF file and get the following response: " + pdf_obs
                        else:
                            other_file = current_download_file[0]
                            shutil.copy(os.path.join(args.download_dir, other_file), task_dir)
                            other_download_obs = f"You downloaded a file: {other_file}"
                    download_files = current_files

                if ele_tag_name == 'button' and ele_type == 'submit':
                    time.sleep(10)

            elif action_key == 'wait':
                time.sleep(5)

            elif action_key == 'type':
                if not args.text_only:
                    type_ele_number = int(info['number'])
                    web_ele = web_eles[type_ele_number]
                else:
                    type_ele_number = info['number']
                    element_box = obs_info[type_ele_number]['union_bound']
                    element_box_center = (element_box[0] + element_box[2] // 2,
                                            element_box[1] + element_box[3] // 2)
                    web_ele = driver_task.execute_script("return document.elementFromPoint(arguments[0], arguments[1]);", element_box_center[0], element_box_center[1])

                warn_obs = exec_action_type(info, web_ele, driver_task)
                if 'wolfram' in task['web']:
                    time.sleep(5)

            elif action_key == 'scroll':
                if not args.text_only:
                    exec_action_scroll(info, web_eles, driver_task, args, None)
                else:
                    exec_action_scroll(info, None, driver_task, args, obs_info)

            elif action_key == 'goback':
                # driver_task.back()
                # time.sleep(2)
                exec_action_goback(task['web'], driver_task)

            elif action_key == 'google':
                driver_task.get('https://www.google.com/')
                time.sleep(2)

            elif action_key == 'answer':
                logging.info(info['content'])
                logging.info('finish!!')
                break

            else:
                raise NotImplementedError
            fail_obs = ""
        except Exception as e:
            logging.error('driver error info:')
            logging.error(str(e))
            if 'element click intercepted' not in str(e):
                fail_obs = "The action you have chosen cannot be exected. Please double-check if you have selected the wrong Numerical Label or Action or Action format. Then provide the revised Thought and Action."
            else:
                fail_obs = ""
            time.sleep(2)

        action_trajectory_json = json.dumps({'action_key':action_key, 'info':info, 'web_else_text':web_eles_text, 'web_text_assist':web_text_assist, 'url_jistory':url_history}, ensure_ascii=False)
        with open(os.path.join(task_dir, 'action_trajectory.json'), 'a', encoding='utf-8') as f:
            f.write(action_trajectory_json+'\n')

        if it%4==0 and args.web_observer:
            observer_help = get_observer_help_from_assistant(client, messages, task['ques'], args.api_model)
            isgoback=False
            if 'NO' in observer_help:
                # go to last page
                # driver_task.back()
                # time.sleep(2)
                isgoback = exec_action_goback(task['web'], driver_task)

            observer_help_json = json.dumps({'it':it, 'observer_help':observer_help,'goback':isgoback}, ensure_ascii=False)
            with open(os.path.join(task_dir, 'observer_help.json'), 'a', encoding='utf-8') as f:
                f.write(observer_help_json+'\n')

    print_message_complete(messages, task_dir)
    driver_task.quit()
    logging.info(f'Total cost: {accumulate_prompt_token / 1000 * 0.01 + accumulate_completion_token / 1000 * 0.03}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_file', type=str, default='data/test.json')
    parser.add_argument('--max_iter', type=int, default=5)
    parser.add_argument("--api_key", default="key", type=str, help="YOUR_OPENAI_API_KEY")
    parser.add_argument("--api_model", default="gpt-4-vision-preview", type=str, help="api model name")
    parser.add_argument("--output_dir", type=str, default='results')
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--max_attached_imgs", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--download_dir", type=str, default="downloads")
    parser.add_argument("--text_only", action='store_true')
    # for AOAI deployment
    parser.add_argument("--api_base", type=str, help="api_base")
    parser.add_argument("--api_type", type=str, help="api_type")
    parser.add_argument("--api_version", type=str, help="api_type")
    # for web browser
    parser.add_argument("--headless", action='store_true', help='The window of selenium')
    parser.add_argument("--save_accessibility_tree", action='store_true')
    parser.add_argument("--force_device_scale", action='store_true')
    parser.add_argument("--window_width", type=int, default=1024)
    parser.add_argument("--window_height", type=int, default=768)  # for headless mode, there is no address bar
    parser.add_argument("--fix_box_color", action='store_true')
    # improvement
    parser.add_argument("--dynamic_load",action='store_true', help='dynamic load web content')
    parser.add_argument("--web_markdown",action='store_true', help='load web html to markdown')
    parser.add_argument("--web_assistant",action='store_true', help='use web assistant to get suggestion')
    parser.add_argument("--web_observer",action='store_true', help='use web observer')

    args = parser.parse_args()

    # OpenAI client
    if args.api_base and args.api_type and args.api_version: # AOAI
        client = AzureOpenAI(api_key=args.api_key,api_version=args.api_version,base_url=args.api_base)
    else:
        if args.api_base:  # openai competiable endpoint          
            client = OpenAI(api_key=args.api_key, base_url=args.api_base)
        else:
            client = OpenAI(api_key=args.api_key)
    options = driver_config(args)

    # Save Result file
    current_time = time.strftime("%Y%m%d_%H_%M_%S", time.localtime())
    result_dir = os.path.join(args.output_dir, current_time)
    os.makedirs(result_dir, exist_ok=True)

    # Load tasks
    tasks = []
    with open(args.test_file, 'r', encoding='utf-8') as f:
        for line in f:
            tasks.append(json.loads(line))


    for task_id in range(len(tasks)):
        task = tasks[task_id]
        execute_task(args, client, options, result_dir, task)
        

if __name__ == '__main__':
    main()
    print('End of process')
