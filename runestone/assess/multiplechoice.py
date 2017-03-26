# Copyright (C) 2013  Bradley N. Miller, Barabara Ericson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
__author__ = 'bmiller'

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst import Directive
from .assessbase import *
import json
import random
from runestone.server.componentdb import addQuestionToDB, addHTMLToDB
from sphinx.addnodes import translatable


class MChoiceNode(nodes.General, nodes.Element, translatable):
    def __init__(self,content, source, line):
        """

        Arguments:
        - `self`:
        - `content`:
        """
        nodes.Element.__init__(self)
        self.mc_options = content
        self.source = source
        self.line = line
        self.mc_translatables = (
            "answer_a", "answer_b", "answer_c", "answer_d", "answer_e",
            "feedback_a", "feedback_b", "feedback_c", "feedback_d", "feedback_e"
            )

    def preserve_original_messages(self):
        "Store a copy of un-translated messages for further reference"
        self.raw_mc_options = self.mc_options.copy()

    def apply_translated_message(self, original_message, translated_message):
        "Replace message with the translation from the catalog (if any)"
        # note that this happens before extraction...
        for key in self.mc_translatables:
            if self.raw_mc_options.get(key) == original_message:
                self.mc_options[key] = translated_message

    def extract_original_messages(self):
        "Return a list of translatable messages (for gettext builder)"
        return [self.raw_mc_options[key]
                for key in self.mc_translatables
                if key in self.raw_mc_options]

def visit_mc_node(self,node):

    node.delimiter = "_start__{}_".format(node.mc_options['divid'])
    self.body.append(node.delimiter)

    res = ""
    if 'random' in node.mc_options:
        node.mc_options['random'] = 'data-random'
    else:
        node.mc_options['random'] = ''
    if 'multiple_answers' in node.mc_options:
        node.mc_options['multipleAnswers'] = 'true'
    else:
        node.mc_options['multipleAnswers'] = 'false'
    res = node.template_start % node.mc_options

    self.body.append(res)

def depart_mc_node(self,node):
    res = ""
    currFeedback = ""
    # Add all of the possible answers
    okeys = list(node.mc_options.keys())
    okeys.sort()
    for k in okeys:
        if 'answer_' in k:
            x,label = k.split('_')
            node.mc_options['alabel'] = label
            node.mc_options['atext'] = "(" +k[-1].upper() + ") " + node.mc_options[k]
            currFeedback = "feedback_" + label
            node.mc_options['feedtext'] = node.mc_options.get(currFeedback,"") #node.mc_options[currFeedback]
            if label in node.mc_options['correct']:
                node.mc_options["is_correct"] = "data-correct"
            else:
                node.mc_options["is_correct"] = ""
            res += node.template_option % node.mc_options


    res += node.template_end % node.mc_options
    self.body.append(res)

    addHTMLToDB(node.mc_options['divid'],
                node.mc_options['basecourse'],
                "".join(self.body[self.body.index(node.delimiter) + 1:]))

    self.body.remove(node.delimiter)






#####################
# multiple choice question with multiple feedback
# author - Barb Ericson
# author - Anusha
class MChoice(Assessment):
    """
.. mchoice:: uniqueid
   :multiple_answers: boolean  [optional]
   :random: boolean [optional]
   :answer_a: possible answer  -- what follows _ is label
   :answer_b: possible answer
   ...
   :answer_e: possible answer
   :correct: letter of correct answer or list of correct answer letters (in case of multiple answers)
   :feedback_a: displayed if a is picked
   :feedback_b: displayed if b is picked
   :feedback_c: displayed if c is picked
   :feedback_d: displayed if d is picked
   :feedback_e: displayed if e is picked

   Question text   ...

    """
    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = True
    has_content = True
    option_spec = RunestoneDirective.option_spec.copy()
    option_spec.update({'answer_a':directives.unchanged,
        'answer_b':directives.unchanged,
        'answer_c':directives.unchanged,
        'answer_d':directives.unchanged,
        'answer_e':directives.unchanged,
        'correct':directives.unchanged,
        'feedback_a':directives.unchanged,
        'feedback_b':directives.unchanged,
        'feedback_c':directives.unchanged,
        'feedback_d':directives.unchanged,
        'feedback_e':directives.unchanged,
        'random':directives.flag,
        'multiple_answers':directives.flag,
    })

    def run(self):
        """
            process the multiplechoice directive and generate html for output.
            :param self:
            :return:
            .. mchoice:: qname
            :multiple_answers: boolean
            :random: boolean
            :answer_a: possible answer  -- what follows _ is label
            :answer_b: possible answer
            ...
            :answer_e: possible answer
            :correct: letter of correct answer or list of correct answer letters (in case of multiple answers)
            :feedback_a: displayed if a is picked
            :feedback_b: displayed if b is picked
            :feedback_c: displayed if c is picked
            :feedback_d: displayed if d is picked
            :feedback_e: displayed if e is picked

            Question text
            ...
            """

        TEMPLATE_START = '''
            <ul data-component="multiplechoice" data-multipleanswers="%(multipleAnswers)s" %(random)s id="%(divid)s">
            '''

        OPTION = '''
            <li data-component="answer" %(is_correct)s id="%(divid)s_opt_%(alabel)s">%(atext)s</li><li data-component="feedback" id="%(divid)s_opt_%(alabel)s">%(feedtext)s</li>
            '''


        TEMPLATE_END = '''

            </ul>
            '''
        addQuestionToDB(self)
        super(MChoice,self).run()




        mcNode = MChoiceNode(self.options, self.srcpath, self.line)
        mcNode.template_start = TEMPLATE_START
        mcNode.template_option = OPTION
        mcNode.template_end = TEMPLATE_END

        self.state.nested_parse(self.content, self.content_offset, mcNode)
        return [mcNode]

#backwards compatibility
class MChoiceMF(MChoice):
    def run(self):
        raise self.error("This directive has been depreciated. Please convert to the new directive 'mchoice'")
        mcmfNode = super(MChoiceMF,self).run()[0]

        return [mcmfNode]

class MChoiceMA(MChoice):
    def run(self):
        self.options['multiple_answers'] = 'multipleAnswers'
        raise self.error("This directive has been depreciated. Please convert to the new directive 'mchoice'")
        mchoicemaNode = super(MChoiceMA,self).run()[0]

        return [mchoicemaNode]

class MChoiceRandomMF(MChoice):
    def run(self):
        self.options['random'] = 'random'
        raise self.error("This directive has been depreciated. Please convert to the new directive 'mchoice'")
        mchoicerandommfNode = super(MChoiceRandomMF,self).run()[0]

        return[mchoicerandommfNode]
