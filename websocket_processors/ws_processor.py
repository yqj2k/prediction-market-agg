from abc import ABC, abstractmethod

class WSProcessor(ABC):
    @abstractmethod
    def createSubcriptionMessage(self):
        raise NotImplementedError("createSubcriptionMessage() must be implemented")
    
    @abstractmethod
    async def processMessage(self, message):
        raise NotImplementedError("processMessage() must be implemented")
