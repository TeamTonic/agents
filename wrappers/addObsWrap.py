import gym
from gym import spaces
import numpy as np

# KeysToDict from KeysToAdd
def keysToDictCalc(keyToAdd, observation_space):
    keysToDict = {}
    for key in keyToAdd:
        elemToAdd = []
        # Loop among all spaces
        for k in observation_space.spaces:
            # Skip frame and consider only a single player
            if k == "frame" or k == "P2":
                continue
            if isinstance(observation_space[k], gym.spaces.dict.Dict):
                for l in observation_space.spaces[k].spaces:
                    if isinstance(observation_space[k][l], gym.spaces.dict.Dict):
                        if key == l:
                            elemToAdd.append("Px")
                            elemToAdd.append(l)
                            keysToDict[key] = elemToAdd
                    else:
                        if key == l:
                            elemToAdd.append("Px")
                            elemToAdd.append(l)
                            keysToDict[key] = elemToAdd
            else:
                if key == k:
                    elemToAdd.append(k)
                    keysToDict[key] = elemToAdd

    return keysToDict

# Positioning element on last frame channel
def addKeys(counter, keyToAdd, keysToDict, obs, newData, playerId):

        dataPos = counter

        for key in keyToAdd:
            tmpList = keysToDict[key]
            if tmpList[0] == "Px":
                val = obs["P{}".format(playerId+1)]

                for idx in range(len(tmpList)-1):

                    if tmpList[idx+1] == "actions":
                        val = np.concatenate((val["actions"]["move"], val["actions"]["attack"]))
                    else:
                        val = val[tmpList[idx+1]]

                    if isinstance(val, (float, int)) or val.size == 1:
                        val = [val]
            else:
                val = [obs[tmpList[0]]]

            for elem in val:
                counter = counter + 1
                newData[counter] = elem

        newData[dataPos] = counter - dataPos

        return counter

# Observation modification (adding one channel to store additional info)
def processObs(obs, dtype, boxHighBound, playerSide, keyToAdd, keysToDict, imitationLearning=False):

    # Adding a channel to the standard image, it will be in last position and it will store additional obs
    shp = obs["frame"].shape
    obsNew = np.zeros((shp[0], shp[1], shp[2]+1), dtype=dtype)

    # Storing standard image in the first channel leaving the last one for additional obs
    obsNew[:,:,0:shp[2]] = obs["frame"]

    # Creating the additional channel where to store new info
    obsNewAdd = np.zeros((shp[0], shp[1], 1), dtype=dtype)

    # Adding new info to the additional channel, on a very
    # long line and then reshaping into the obs dim
    newData = np.zeros((shp[0] * shp[1]))

    # Adding new info for 1P
    counter = 0
    addKeys(counter, keyToAdd, keysToDict, obs, newData, playerId=0)

    # Adding new info for P2 in 2P games
    if playerSide == "P1P2" and not imitationLearning:
        counter = int((shp[0] * shp[1]) / 2)
        addKeys(counter, keyToAdd, keysToDict, obs, newData, playerId=1)

    newData = np.reshape(newData, (shp[0], -1))

    newData = newData * boxHighBound

    obsNew[:,:,shp[2]] = newData

    return obsNew

# Convert additional obs to fifth observation channel for stable baselines
class AdditionalObsToChannel(gym.ObservationWrapper):
    def __init__(self, env, keyToAdd, imitationLearning=False):
        """
        Add to observations additional info
        :param env: (Gym Environment) the environment to wrap
        :param keyToAdd: (list) ordered parameters for additional Obs
        """
        gym.ObservationWrapper.__init__(self, env)
        shp = self.env.observation_space["frame"].shape
        self.keyToAdd = keyToAdd
        self.imitationLearning = imitationLearning

        self.boxHighBound = self.env.observation_space["frame"].high.max()
        self.boxLowBound = self.env.observation_space["frame"].low.min()
        assert (self.boxHighBound == 1.0 or self.boxHighBound == 255),\
                "Observation space max bound must be either 1.0 or 255 to use Additional Obs"
        assert (self.boxLowBound == 0.0 or self.boxLowBound == -1.0),\
                "Observation space min bound must be either 0.0 or -1.0 to use Additional Obs"

        # Build keyToAdd - Observation Space dict connectivity
        self.keysToDict = keysToDictCalc(self.keyToAdd, self.env.observation_space)

        self.oldObsSpace = self.observation_space
        self.observation_space = spaces.Box(low=self.boxLowBound, high=self.boxHighBound,
                                            shape=(shp[0], shp[1], shp[2] + 1),
                                            dtype=np.float32)
        self.shp = self.observation_space.shape

        # Return keyToAdd count
        self.keyToAddCount = []
        for key in self.keyToAdd:
            p1Val = addKeys(0, [key], self.keysToDict, self.oldObsSpace.sample(),
                            np.zeros((shp[0] * shp[1])),0)
            if self.env.playerSide == "P1P2":
                p2Val = addKeys(0, [key], self.keysToDict, self.oldObsSpace.sample(),
                                np.zeros((shp[0] * shp[1])),1)
                self.keyToAddCount.append([p1Val, p2Val])
            else:
                self.keyToAddCount.append([p1Val])

    # Process observation
    def observation(self, obs):

        return processObs(obs, self.observation_space.dtype, self.boxHighBound,
                          self.env.playerSide, self.keyToAdd, self.keysToDict, self.imitationLearning)