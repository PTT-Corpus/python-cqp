# -*- coding: utf8 -*-
"""A Python wrapper of PyCQP_interface."""
import logging

from CWB.CL import Corpus
import PyCQP_interface

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CQPself:
    """Wrap for `cqp` commandline utility.

    :param: corpus: name of the corpus
    """

    def __init__(self, bin_path, corpus_name, registry_dir):
        """Build `cqp` connection.

        :bin_path: absolute path of `cqp` bin (usually `/usr/local/bin/cqp`)
        :param: corpus_name: name of the corpus
        :param: registry_dir: absolute path of `cqp` registry directory
        """
        cqp = PyCQP_interface.CQP(
            bin=bin_path,
            options=f'-c -r {registry_dir} -D {corpus_name}'
        )
        corpus = Corpus(corpus_name, registry_dir=registry_dir)
        self.cqp = cqp
        self.corpus = corpus

    def __del__(self):
        """Destroy `cqp` connection."""
        try:
            self.cqp.Terminate()
        except Exception as e:
            logger.warning(e)

    def make_conc(
            self, query, page_num=1, num_per_page=50, show_pos=False,
            begin_time=None, end_time=None, board_list=None, window_size=6):
        """Make concordance."""
        conclist = []

        last = num_per_page * page_num - 1
        first = last - num_per_page + 1

        self.cqp.Exec('[word="%s"];' % query)

        total = self.cqp.Exec("size Last;")
        self.results = self.cqp.Dump(first=first, last=last)
        if self.results == [['']]:
            return None

        words = self.corpus.attribute(b"word", "p")
        if show_pos is True:
            postags = self.corpus.attribute(b"pos", "p")
        elif show_pos is False:
            pass
        else:
            raise
        boards = self.corpus.attribute(b"text_board", "s")
        ptimes = self.corpus.attribute(b"text_time", "s")
        for line in self.results:
            output = dict()
            start = int(line[0])
            end = int(line[1]) + 1

            # post_time filter
            ptime = ptimes.find_pos(start)[-1]
            if begin_time is not None and end_time is not None:
                if begin_time <= int(ptime) <= end_time:
                    pass
                else:
                    continue
            elif begin_time is not None and end_time is None:
                if int(ptime) < begin_time:
                    continue

            elif begin_time is None and end_time is not None:
                if int(ptime) > end_time:
                    continue

            # board_list filter
            board = boards.find_pos(start)[-1]

            if board_list:
                if board not in board_list:
                    continue

            lw = words[start - window_size:start]
            rw = words[end:end + window_size]
            qw = words[start:end]

            if show_pos is True:
                lp = postags[start - window_size:start]
                rp = postags[end:end + window_size]
                qp = postags[start:end]

                left = ['%s/%s' % (word, pos) for word, pos in zip(lw, lp)]
                mid = ['%s/%s' % (word, pos) for word, pos in zip(qw, qp)]
                right = ['%s/%s' % (word, pos) for word, pos in zip(rw, rp)]

            elif show_pos is False:
                left = ' '.join(lw)
                mid = ' '.join(qw)
                right = ' '.join(rw)

            output['conc'] = (left, mid, right)
            output['board'] = board
            output['time'] = ptime
            conclist.append(output)
        fin = {
            'total': total,
            'num_per_page': num_per_page,
            'conclist': conclist
        }
        return fin
