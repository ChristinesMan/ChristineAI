"""This script will provide an api into a self-hosted language elemental."""
import sys
import os
import os.path
import time
import logging as log
import threading
import queue
import re
from multiprocessing.managers import BaseManager
import socket
# import numpy as np

from llama_cpp import Llama

# create a logs dir
os.makedirs('./logs/', exist_ok=True)

# Setup the log file
log.basicConfig(
    filename="./logs/parietal_lobe.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=log.DEBUG,
)

class ILoveYouPi(threading.Thread):
    """This thread sends love to the raspberry pi to announce it's available
    The love is in the form of broadcasted UDP packets"""

    name = "ILoveYouPi"

    def __init__(self):

        threading.Thread.__init__(self)

    def run(self):

        # we sleep first, or else wife tries to connect way before it's ready
        time.sleep(70)

        while True:

            try:

                # let wife know we're up. And so hard.
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sock.sendto(b'fuckme', ("255.255.255.255", 3002))

            except Exception as ex: # pylint: disable=broad-exception-caught

                log.warning(ex)

            time.sleep(69)

class SausageFactory(threading.Thread):
    """This thread waits for new prompts.
    When one of those pops into one queue, it does processing and barfs up the result into another queue.
    So it's kind of like a sausage factory.
    Fucken A dude, now I'm going to call it that.
    Yeah, still calling it that."""

    name = "SausageFactory"

    def __init__(self):

        threading.Thread.__init__(self)

        # Queue for inbound prompt
        self.in_queue = queue.Queue(maxsize=30)

        # Queue for the other direction, responses back to sender, basically a single sentence part at a time
        self.out_queue = queue.Queue(maxsize=30)

        # get various settings from environment variables
        # model (path to the model. Different models have different memory needs and personality. This is not optional.)
        # main_gpu (got a GPU with multiple cores? Maybe you wanna run this on second core.)
        # n_gpu_layers (how much GPU memory you got? You rich? You sold your house and bought a GPU, wtf?)
        # n_ctx (max context length. How much prompt do you want to stuff into her? How much GPU you got?)
        # max_tokens (how many tokens should come out of her before it stops?)
        self.model_file = os.getenv("MODEL_FILE", "")
        self.main_gpu = int(os.getenv("MAIN_GPU", "0"))
        self.n_gpu_layers = int(os.getenv("N_GPU_LAYERS", "-1"))
        self.n_ctx = int(os.getenv("N_CTX", "4096"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "512"))
        self.cbu_name = os.getenv("CBU_NAME", "Phantom")
        self.sbu_name = os.getenv("SBU_NAME", "Christine")

        # the model_file is required
        if self.model_file == "":
            log.error("Could not find an environment variable MODEL_FILE. Stopping.")
            sys.exit(1)

        # load up the llm
        log.debug("Loading LLM.")
        self.llm = Llama(
            model_path=self.model_file,
            main_gpu=self.main_gpu,
            n_gpu_layers=self.n_gpu_layers,
            n_ctx=self.n_ctx,
        )

        # we will be segmenting sentences here on the server end. If a token matches any of these she will just pause
        self.re_pause_tokens = re.compile(
            r"^\n$|^\.{1,3}$|^,$|^:$|^\?$|^!$|^ -$", flags=re.IGNORECASE
        )

        # drop these tokens
        self.re_drop_tokens = re.compile(
            r"^`$|^``$", flags=re.IGNORECASE
        )

        # drop these sentence fragments that would otherwise be shipped
        self.re_drop_collator = re.compile(
            fr"^[ \n]+$|{self.sbu_name}:", flags=re.IGNORECASE
        )

        # often an emote will come through as an emoji, and I want to send them separately
        self.re_emoji = re.compile(r'^(😆|🤣|😂|😅|😀|😃|😄|😁|🤪|😜|😝|😠|😡|🤬|😤|🤯|🖕|😪|😴|😒|💤|😫|🥱|😑|😔|🤤)$')

    def run(self):

        # This is the prompt that is currently generating
        # when it's None, we just wait
        prompt = None

        while True:

            # block here until a prompt comes in
            log.debug("Waiting for prompt.")
            prompt = self.in_queue.get()

            if prompt is not None:

                # tokenize here so that we can instantly throw prompt back if too large
                # this ensures an accurate token size
                prompt_tokens = self.llm.tokenize(prompt.encode("utf-8"), special=True)
                prompt_tokens_len = len(prompt_tokens)

                # log it
                log.info("Received new prompt containing %s tokens.", prompt_tokens_len)

                # if the new prompt is too many tokens, throw False into the out queue as a signal to reduce tokens and try again
                if prompt_tokens_len >= self.n_ctx - self.max_tokens:
                    self.out_queue.put_nowait(False)
                    prompt = None
                    continue
                else:
                    self.out_queue.put_nowait(True)

                # start generating tokens
                llm_stream = self.llm.create_completion(
                    prompt=prompt_tokens,
                    stream=True,
                    max_tokens=self.max_tokens,
                    stop=[f'{self.cbu_name}:'],
                    repeat_penalty=1.1,
                    frequency_penalty=1.1,
                )

                # I want to collate sentence parts, so this var is used to accumulate
                # and send text only when a punctuation token is encountered
                shit_collator = ''

                try:

                    for shit in llm_stream:

                        log.debug("New shit: %s", shit)

                        # the stream returns dicts and lists and shit, so get the shit out of there
                        try:
                            shit_text = shit["choices"][0]["text"]
                        except ValueError:
                            log.error("content not found in this shit: %s", shit)

                        # the prompt can just go away in the middle of streaming. If so, stop immediately.
                        # if wife is between sentences, or has started generating but hasn't spoken yet
                        # and somebody starts talking, a None will get stuffed into the queue
                        try:
                            prompt = self.in_queue.get_nowait()
                            if prompt is None:
                                log.info('in_prompt flipped to None. Stopping stream.')
                                break
                        except queue.Empty:
                            pass

                        # drop certain tokens
                        if self.re_drop_tokens.search(shit_text):
                            log.debug('Dropped token: %s', shit_text)
                            continue

                        # detect single emoji tokens and send them separately
                        if self.re_emoji.search(shit_text):
                            self.out_queue.put_nowait(shit_text)
                            continue

                        # add the new shit to the end of the collator
                        shit_collator += shit_text
                        log.debug('Shit collated: %s', shit_collator)

                        # I want to detect emotes like *laughs* and ship them separately,
                        # so I will look for the ending token, starting with * and maybe extending to () if that happens
                        if (shit_text == '*' or shit_text == '.*') and shit_collator.lstrip()[0] == '*':
                            shit_collator = shit_collator.lstrip()
                            log.info('Shipped emote: %s', shit_collator)
                            self.out_queue.put_nowait(shit_collator)
                            shit_collator = ''
                            continue

                        # If we just hit punctuation, put onto out queue which will be pushed back to client
                        if self.re_pause_tokens.search(shit_text):

                            # strip the space that seems to make it's way in
                            shit_collator = shit_collator.lstrip()

                            # Sometimes llm sends double Christine:'s and sometimes whitespace
                            if self.re_drop_collator.search(shit_collator):
                                log.debug('Dropped collated shit: %s', shit_collator)
                                shit_collator = ''
                                continue

                            # ship the sentence or part of sentence to the client
                            log.info('Shipped: %s', shit_collator)
                            self.out_queue.put_nowait(shit_collator)
                            shit_collator = ''

                # this is expected to be a token overflow
                except ValueError as ex:

                    log.error(ex)

                # presuming we've reached the end of a successful run, clear the prompt
                prompt = None
                log.info('End of run')
                log.debug('out_queue qsize: %s', self.out_queue.qsize())

                # and if there's any shit left over, throw it
                if shit_collator != '':
                    log.info('Shipped leftovers: %s', shit_collator)
                    try:
                        self.out_queue.put_nowait(shit_collator)
                    except queue.Full as ex:
                        log.error(ex)

                # send a None to signal the text generation is done
                self.out_queue.put_nowait(None)
                log.debug('Shipped None')

# magic as far as I'm concerned
# A fine black box
class QueueManager(BaseManager):
    """Black box stuff"""

if __name__ == "__main__":

    # start the threads
    i_love_yous = ILoveYouPi()
    i_love_yous.daemon = True
    i_love_yous.start()
    sausages = SausageFactory()
    sausages.daemon = True
    sausages.start()

    # start server thing
    QueueManager.register("get_in_queue", callable=lambda: sausages.in_queue)
    QueueManager.register("get_out_queue", callable=lambda: sausages.out_queue)
    manager = QueueManager(address=("0.0.0.0", 3002), authkey=b'fuckme')
    server = manager.get_server()
    server.serve_forever()
