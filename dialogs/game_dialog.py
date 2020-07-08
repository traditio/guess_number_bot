# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from random import randint, randrange

from botbuilder.core import MessageFactory, UserState, ConversationState
from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import (
    NumberPrompt,
    ConfirmPrompt,
    PromptOptions,
    PromptValidatorContext,
)


class ChoiceDialog(ComponentDialog):
    def __init__(self, dialog_id: str = None):
        super(ChoiceDialog, self).__init__(dialog_id or ChoiceDialog.__name__)

        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.selection_step,
                    self.loop_step
                ]
            )
        )
        self.add_dialog(
            NumberPrompt(NumberPrompt.__name__, ChoiceDialog.number_validator)
        )

    @staticmethod
    async def number_validator(ctx: PromptValidatorContext = None) -> bool:
        return ctx.recognized.succeeded and 0 <= ctx.recognized.value <= 10

    async def selection_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # WaterfallStep always finishes with the end of the Waterfall or with another dialog;
        # here it is a Prompt Dialog. Running a prompt here means the next WaterfallStep will
        # be run when the users response is received.

        if step_context.options is None:
            raise Exception("internal error, number not passed in")

        step_context.values["number"] = step_context.options

        return await step_context.prompt(
            NumberPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Please enter number")
            ),
        )

    async def loop_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result == step_context.values["number"]:
            return await step_context.end_dialog(True)

        if step_context.result > step_context.values["number"]:
            await step_context.context.send_activity(MessageFactory.text("The number is too high."))
        elif step_context.result < step_context.values["number"]:
            await step_context.context.send_activity(MessageFactory.text("The number is too low."))

        return await step_context.replace_dialog(ChoiceDialog.__name__, step_context.options)


class GameDialog(ComponentDialog):
    def __init__(self, conversation_state: ConversationState, user_state: UserState):
        super(GameDialog, self).__init__(GameDialog.__name__)

        self.game = conversation_state.create_property("Game")

        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.welcome_step,
                    self.acknoweledge,
                    self.play_again,
                ],
            ))

        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(ChoiceDialog(ChoiceDialog.__name__))

        self.initial_dialog_id = WaterfallDialog.__name__

    async def welcome_step(
            self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:

        number = randrange(0, 11)

        step_context.values["number"] = number
        return await step_context.begin_dialog(ChoiceDialog.__name__, number)

    async def acknoweledge(
            self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:

        await step_context.context.send_activity(
            MessageFactory.text(f"Congratulations! You won. The number was {step_context.values['number']}"))

        return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Would you like to play again?")
            ))

    async def play_again(
            self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        if step_context.result:
            return await step_context.replace_dialog(GameDialog.__name__)
        else:
            await step_context.context.send_activity(
                MessageFactory.text("Thank you for playing!!!"))
            return await step_context.end_dialog(True)

    @staticmethod
    def number_validator(prompt_context: PromptValidatorContext) -> bool:
        return (
                prompt_context.recognized.succeeded
                and 0 <= prompt_context.recognized.value <= 10
        )
