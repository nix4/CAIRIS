#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an
#  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
#  specific language governing permissions and limitations
#  under the License.


from xml.sax.handler import ContentHandler,EntityResolver
from AssetParameters import AssetParameters
import AssetParametersFactory
from AttackerParameters import AttackerParameters
from AttackerEnvironmentProperties import AttackerEnvironmentProperties
from VulnerabilityParameters import VulnerabilityParameters
from VulnerabilityEnvironmentProperties import VulnerabilityEnvironmentProperties
from ThreatParameters import ThreatParameters
from ThreatEnvironmentProperties import ThreatEnvironmentProperties
from MisuseCaseEnvironmentProperties import MisuseCaseEnvironmentProperties
from MisuseCase import MisuseCase
from RiskParameters import RiskParameters

from Borg import Borg

def a2i(spLabel):
  if spLabel == 'Low':
    return 1
  elif spLabel == 'Medium':
    return 2
  elif spLabel == 'High':
    return 3
  else:
    return 0

def it2Id(itLabel):
  if itLabel == 'required':
    return 1
  else:
    return 0

class AttackPatternContentHandler(ContentHandler,EntityResolver):
  def __init__(self):
    self.thePatternName = ''
    self.theLikelihood = ''
    self.theSeverity = ''
    self.inIntent = 0
    self.theIntent = ''
    self.theMotivations = []
    self.theEnvironment = ''
    self.theAttack = ''
    self.theExploit = ''
    self.theParticipants = []
    self.theTargets = []
    self.theExploits = []
    self.inConsequences = 0
    self.theConsequences = ''
    self.inImplementation = 0
    self.theImplementation = ''
    self.inKnownUses = 0
    self.theKnownUses = ''
    self.inRelatedPatterns = 0
    self.theRelatedPatterns = ''
    b = Borg()
    self.configDir = b.configDir
    self.dbProxy = b.dbProxy

    self.theAssetParameters = []
    self.theAttackerParameters = []
    self.theVulnerabilityParameters = None
    self.theThreatParameters = None
    self.theRiskParameters = None

    self.resetMotivationElements()
    self.resetParticipantElements()

  def assets(self): return self.theAssetParameters
  def attackers(self): return self.theAttackerParameters
  def vulnerability(self): return self.theVulnerabilityParameters
  def threat(self): return self.theThreatParameters
  def risk(self): return self.theRiskParameters

  def resetMotivationElements(self):
    self.theGoal = ''
    self.theValue = 'None'
    self.inDescription = 0
    self.theDescription = ''

  def resetParticipantElements(self):
    self.theParticipant = ''
    self.theMotives = []
    self.theResponsibilities = []
     
  def resolveEntity(self,publicId,systemId):
    return self.configDir + '/component_view.dtd'

  def startElement(self,name,attrs):
    if (name == 'attack_pattern'):
      self.thePatternName = attrs['name']
      self.theLikelihood = attrs['likelihood']
      self.theSeverity = attrs['severity']
    elif (name == 'intent'):
      self.inIntent = 1
      self.theIntent = ''
    elif (name == 'motivation'):
      self.theGoal = attrs['goal']
      self.theValue = attrs['value']
    elif (name == 'description'):
      self.inDescription = 1
      self.theDescription = ''
    elif (name == 'applicability'):
      self.theEnvironment = attrs['environment']
    elif (name == 'structure'):
      self.theAttack = attrs['attack']
      self.theExploit = attrs['exploit']
    elif (name == 'participant'):
      self.theParticipant = attrs['name']
    elif (name == 'motive'):
      self.theMotives.append(attrs['name'])
    elif (name == 'responsibility'):
      self.theResponsibilities.append((attrs['name'],attrs['value']))
    elif (name == 'target'):
      self.theTargets.append(attrs['name'])
    elif (name == 'exploit'):
      self.theExploits.append(attrs['name'])
    elif (name == 'consequences'):
      self.inConsequences = 1
      self.theConsequences = ''
    elif name == 'implementation':
      self.inImplementation = 1
      self.theImplementation = ''
    elif name == 'known_uses':
      self.inKnownUses = 1
      self.theKnownUses = ''
    elif name == 'related_patterns':
      self.inRelatedPatterns = 1
      self.theRelatedPatterns = ''

  def characters(self,data):
    if self.inIntent:
      self.theIntent += data
    elif self.inDescription:
      self.theDescription += data
    elif self.inConsequences:
      self.theConsequences += data
    elif self.inImplementation:
      self.theImplementation += data
    elif self.inKnownUses:
      self.theKnownUses += data
    elif self.inRelatedPatterns:
      self.theRelatedPatterns += data


  def endElement(self,name):
    if name == 'intent':
      self.inIntent = 0
    elif name == 'motivation':
      self.theMotivations.append((self.theGoal,self.theValue,self.theDescription))
      self.resetMotivationElements()
    elif name == 'participant':
      self.theParticipants.append((self.theParticipant,self.theMotives,self.theResponsibilities))
      self.resetParticipantElements()
    elif name == 'description':
      self.inDescription = 0
    elif name == 'consequences':
      self.inConsequences = 0
    elif name == 'implementation':
      self.inImplementation = 0
    elif name == 'known_uses':
      self.inKnownUses = 0
    elif name == 'related_patterns':
      self.inRelatedPatterns = 0
    elif name == 'attack_pattern':
      assetList = self.theTargets + self.theExploits
      for assetName in assetList:
        self.theAssetParameters.append(AssetParametersFactory.buildFromTemplate(assetName,[self.theEnvironment]))

      attackerNames = []
      for attackerName,attackerMotives,attackerCapabilities in self.theParticipants:
        attackerRoles = self.dbProxy.dimensionRoles(self.dbProxy.getDimensionId(attackerName,'persona'),self.dbProxy.getDimensionId(self.theEnvironment,'environment'),'persona')
        ep = AttackerEnvironmentProperties(self.theEnvironment,attackerRoles,attackerMotives,attackerCapabilities)
        p = AttackerParameters(attackerName,'','',[],[ep])
        self.theAttackerParameters.append(p) 
        attackerNames.append(attackerName)
  
      
      vp = VulnerabilityEnvironmentProperties(self.theEnvironment,self.theSeverity,self.theExploits)
      vulRows = self.dbProxy.getVulnerabilityDirectory(self.theExploit)
      vulData = vulRows[0]
      self.theVulnerabilityParameters = VulnerabilityParameters(self.theExploit,vulData[2],vulData[3],[],[vp])

      spDict = {}
      spDict['confidentiality'] = (0,'None')
      spDict['integrity'] = (0,'None')
      spDict['availability'] = (0,'None')
      spDict['accountability'] = (0,'None')
      spDict['anonymity'] = (0,'None')
      spDict['pseudonymity'] = (0,'None')
      spDict['unlinkability'] = (0,'None')
      spDict['unobservability'] = (0,'None')

      for thrMotivation in self.theMotivations:
        spName = thrMotivation[0]
        spValue = thrMotivation[1]
        spRationale = thrMotivation[2]
        spDict[spName] = (a2i(spValue),spRationale)
      
      cProperty,cRationale = spDict['confidentiality']
      iProperty,iRationale = spDict['integrity']
      avProperty,avRationale = spDict['availability']
      acProperty,acRationale = spDict['accountability']
      anProperty,anRationale = spDict['anonymity']
      panProperty,panRationale = spDict['pseudonymity']
      unlProperty,unlRationale = spDict['unlinkability']
      unoProperty,unoRationale = spDict['unobservability']

      tp = ThreatEnvironmentProperties(self.theEnvironment,self.theLikelihood,self.theTargets,attackerNames,[cProperty,iProperty,avProperty,acProperty,anProperty,panProperty,unlProperty,unoProperty],[cRationale,iRationale,avRationale,acRationale,anRationale,panRationale,unlRationale,unoRationale])
      thrRows = self.dbProxy.getThreatDirectory(self.theAttack)
      thrData = thrRows[0]
      self.theThreatParameters = ThreatParameters(self.theAttack,thrData[3],thrData[2],[],[tp])

      rep = MisuseCaseEnvironmentProperties(self.theEnvironment,self.theImplementation )
      mc = MisuseCase(-1,'Exploit ' + self.thePatternName,[rep],self.thePatternName)
      self.theRiskParameters = RiskParameters(self.thePatternName,self.theAttack,self.theExploit,mc,[])
