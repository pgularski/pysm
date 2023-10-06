""" A simple example that uses the states-are-classes pattern and demonstrates retrievable substates """

import enum
import pysm
import logging

logger = logging.getLogger(__name__)


class CdEvent(enum.Enum):
    PLAY = enum.auto()
    OPEN_CLOSE = enum.auto()
    STOP = enum.auto()
    CD_DETECTED = enum.auto()
    PAUSE = enum.auto()
    END_PAUSE = enum.auto()
    HAMMER = enum.auto()


class HybridState(pysm.State):
    """ Leaf states that know how to interact with the controller """

    def __init__(self, controller):
        super().__init__(self.__class__.__name__)
        # keep an instance of the controller so that we can actually do things
        self._controller = controller

    def _on_enter(self, state, event):
        logger.info(f'Entered state {state.name}')

    def _on_exit(self, state, event):
        logger.info(f'Exited state {state.name}')

    def _on_tick(self, state, event):
        """ Respond to 'tick' event while we are in each state """
        logger.info(f'Received tick in state {state.name}')

    def register_handlers(self):
        self.handlers = {'enter': self._on_enter,
                         'exit': self._on_exit,
                         'tick': self._on_tick}


class HybridSuperState(pysm.StateMachine):
    """ Super-states (composite states) that know how to interact with the controller """

    def __init__(self, controller):
        super().__init__(self.__class__.__name__)
        # keep an instance of the controller so that we can actually do things
        self._controller = controller

    def _on_enter(self, state, event):
        """ Default entry action is just to log the entry """
        logger.info(f'Entered state {state.name}')

    def _on_exit(self, state, event):
        """ Default exit action is just to log the exit"""
        logger.info(f'Exited state {state.name}')

    def _on_tick(self, state, event):
        """ Respond to 'tick' event while we are in each state """
        logger.info(f'Received tick in state {state.name}')

    def register_handlers(self):
        self.handlers = {'enter': self._on_enter,
                         'exit': self._on_exit,
                         'tick': self._on_tick}


class CdPlayer(HybridSuperState):
    """ The one-and-only top-level state (machine) """

    def __init__(self, controller):
        super().__init__(controller)

        self.add_state(NotBroken(controller), initial=True)
        self.add_state(Broken(controller))

        # I believe that this is interpreted with local (as opposed to external) transition syntax
        # https://en.wikipedia.org/wiki/UML_state_machine#Local_versus_external_transitions
        # TODO: Consider modifying psym library to support this
        self.add_transition(from_state=self, to_state=self.substate('Broken'), events=[CdEvent.HAMMER])

        # Final step
        self.initialize()

    def dispatch(self, event):
        logger.info(f'Dipatching {event}...')
        super().dispatch(pysm.Event(event))

    def tick(self):
        logger.info('Injecting tick...')
        super().dispatch(pysm.Event('tick'))


class Broken(HybridSuperState):
    pass


class NotBroken(HybridSuperState):
    pass

    def __init__(self, controller):
        super().__init__(controller)
        self.add_state(Stopped(controller), initial=True)
        self.add_state(Open(controller))
        self.add_state(Empty(controller))
        self.add_state(Playing(controller))
        self.add_state(Paused(controller))

        # I would MUCH rather define these transitions as part of the origin state's class!
        # This feels like I have to define everything one level higher than I would like.
        self.add_transition(from_state=self.substate('Stopped'), to_state=self.substate('Playing'), events=[CdEvent.PLAY])
        self.add_transition(from_state=self.substate('Stopped'), to_state=self.substate('Open'), events=[CdEvent.OPEN_CLOSE])

        self.add_transition(from_state=self.substate('Open'), to_state=self.substate('Empty'), events=[CdEvent.OPEN_CLOSE])

        self.add_transition(from_state=self.substate('Empty'), to_state=self.substate('Open'), events=[CdEvent.OPEN_CLOSE])
        self.add_transition(from_state=self.substate('Empty'), to_state=self.substate('Stopped'), events=[CdEvent.CD_DETECTED])

        self.add_transition(from_state=self.substate('Playing'), to_state=self.substate('Stopped'), events=[CdEvent.STOP])
        self.add_transition(from_state=self.substate('Playing'), to_state=self.substate('Paused'), events=[CdEvent.PAUSE])
        self.add_transition(from_state=self.substate('Playing'), to_state=self.substate('Open'), events=[CdEvent.OPEN_CLOSE])

        self.add_transition(from_state=self.substate('Paused'), to_state=self.substate('Stopped'), events=[CdEvent.STOP])
        self.add_transition(from_state=self.substate('Paused'), to_state=self.substate('Playing'), events=[CdEvent.PLAY])
        self.add_transition(from_state=self.substate('Paused'), to_state=self.substate('Open'), events=[CdEvent.OPEN_CLOSE])


class Stopped(HybridState):

    def _on_stop(self, state, event):
        """ Just an example of how a state can handle an event without a transition """
        logger.info('Received redundant STOP event')

    def register_handlers(self):
        self.handlers[CdEvent.STOP] = self._on_stop

class Open(HybridState):
    pass


class Empty(HybridState):
    pass

class Playing(HybridState):
    pass


class Paused(HybridState):
    pass


class DummyController:
    pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    controller = DummyController()
    cd_player = CdPlayer(controller)

    cd_player.dispatch(CdEvent.PLAY)
    cd_player.tick()

    cd_player.dispatch(CdEvent.PAUSE)
    cd_player.tick()

    cd_player.dispatch(CdEvent.PLAY)
    cd_player.tick()

    cd_player.dispatch(CdEvent.HAMMER)
    cd_player.tick()

