import pybgpstream
from itertools import groupby
from collections import defaultdict
import os
import re
import numpy as np
import copy
import time
# if run script in jupyter notebook
from tqdm.notebook import trange, tqdm
#if run script in python script
#from tqdm import trange, tqdm
import pandas as pd
import json
from datetime import datetime, timedelta


from LLM_Module import LLM_Module


class BEAR_few_collector(LLM_Module):
    '''
    BEAR (BGP Event Analysis and Reporting) object.
    given detected time, IP/Target AS, extract AS paths from history routing table data, BGP messages before event, BGP messages after event
    feed them to llm
    '''
    def __init__(self, collector_list, model = "gpt-4o", project = "rcc", save_path = "e/", read_path = None, n_collector = 24):
        '''
        initialize llm, collector_list, collector project, saving path and read path
        Args:
            collector_list: list of collector names where we collect BGP data to write report
            model: backbone llm, default is gpt-4o
            project: which project that the collector we use is coming from. (for bgpstream)
            save_path: directory to save results/reports
            read_path: if provided, we read BGP data from this directory instead of using bgpstream to retrieve BGP data (if we already
                        retrieved relevant BGP data before and saved here)
        '''
        super().__init__(model=model) #initialize LLM module
        self.n_collector = n_collector
        self.collector_list = collector_list
        self.model = model
        self.project = project
        self.save_path = save_path #directory to save files
        if not read_path:
            read_path = save_path
        self.read_path = read_path
        os.makedirs(save_path, exist_ok=True)

    def generate_multi_event(self, data_path):
        '''
        generate report for each event recorded in data_path
        Args:
            data_path: path to a csv file that records the information for each detected BGP anomaly event
        '''
        data = pd.read_csv(data_path, na_filter=False)
        N = len(data)
        for i in trange(N):
            #note that currently, event 9 and event 20 are the two events that exceeds token limit
            if i == 9 or i == 20:
                continue
            event = data.iloc[i]
            start_time = event['Start'].split(';')[0] if event['Start'] else None
            IP = event['IP'].split(';')[0] if event['IP'] else None
            AS = event['AS'].split(';')[0] if event['AS'] else None
            end_time = event['End'].split(';')[0] if event['End'] else None
            event_type = event['Event Type'].split(';')[0] if event['Event Type'] else None
            self.generate_single_event(start_time=start_time, file_save_prefix=str(i)+"_", IP=IP, AS=AS, end_time=end_time, Event_Type=event_type)
            break
        return None
            
    def generate_single_event(self, start_time, file_save_prefix="", IP=None, AS=None, end_time=None, Event_Type=None):
        '''
        generate report for a single event
        Args:
            start_time: time when the anomaly event starts
            file_save_prefix: prefix to add to file name of all the result file for this event
            IP: victim IP prefix
            AS: victim AS
            end_time: time when the anomaly event ends
            Event_Type: type of the event (unused in the current code)
        '''
        if IP: #all of our experiment assume victim IP available
            '''if IP is provided'''
            try: #read BGP data from read_path
                with open(self.read_path + file_save_prefix + "history_rib.json", "r") as f:
                    history_rib = json.load(f)
                with open(self.read_path + file_save_prefix + "before_event_rib.json", "r") as f:
                    rib_before_incident = json.load(f)
                with open(self.read_path + file_save_prefix + "after_event_rib.json", "r") as f:
                    rib_after_incident = json.load(f)
            except: #if BGP data not provided, retrieve them from BGPStream
                history_rib, rib_before_incident, rib_after_incident = self.AS_Path_IP(start_time=start_time, IP_prefix=IP, end_time = end_time)

            
            chosed_collectors = random.choices(self.collector_list, k=self.n_collector)
            rib_before_incident = {i:rib_before_incident[i] for i in chosed_collectors}
            rib_after_incident = {i:rib_after_incident[i] for i in chosed_collectors}
            
            
            try: #to automatically skip event with data exceeds llm token limit
                report, report_dict = self.generate_report(history_rib=history_rib,
                                              rib_before_incident=rib_before_incident,
                                              rib_after_incident=rib_after_incident,
                                              time=start_time,
                                              IP=IP,
                                             Event_Type=Event_Type)
                with open(self.save_path + file_save_prefix + "report.txt", "w") as f:
                    json.dump(report, f) #final report
                with open(self.save_path + file_save_prefix + "reprot_dict.json", "w") as f:
                    json.dump(report_dict, f) #includes intermediate results
            except:
                return None
            
        elif AS: #not using
            '''IP not available but target AS available'''
            history_rib, rib_before_incident, rib_after_incident = self.AS_Path_AS(start_time=start_time, target_AS=AS, end_time = end_time)
            report = self.generate_report(history_rib=history_rib,
                                          rib_before_incident=rib_before_incident,
                                          rib_after_incident=rib_after_incident,
                                          time=start_time,
                                          AS=AS)
        else:
            raise("Must provide IP or AS")
        ###save routing table and report
        # with open(self.save_path + file_save_prefix + "history_rib.json", "w") as f:
        #     json.dump(history_rib, f)
        # with open(self.save_path + file_save_prefix + "before_event_rib.json", "w") as f:
        #     json.dump(rib_before_incident, f)
        # with open(self.save_path + file_save_prefix + "after_event_rib.json", "w") as f:
        #     json.dump(rib_after_incident, f)
        
            
        return None

    def AS_Path_IP(self, start_time, IP_prefix, end_time = None):
        '''
        provide target IP and time extract BGP data, end time is optional
        '''
        # convert start time to datetime object
        start = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        #convert end time to datetime object
        if end_time: #if end time is provided
            end = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        else: #default 1 day after start
            end = start + timedelta(days=1)


        ###extract history routing table
        history_rib = defaultdict(dict)
        for collector in tqdm(self.collector_list):
            #rcc collects rib every 8 hours, we pick the 2nd last checkpoint
            stream = pybgpstream.BGPStream(
                from_time=str(start-timedelta(hours=16)), until_time=str(start-timedelta(hours=8)),
                collectors=[collector],
                record_type="ribs",
                filter = f"prefix any {IP_prefix}"  #collect as path to ip prefix that are less or more specific to the target IP prefix
            )
            as_path = defaultdict(dict)

            for rec in tqdm(stream.records()):
                for ele in rec:
                    # Get the peer ASn
                    peer = str(ele.peer_asn)
                    hops = [k for k, g in groupby(ele.fields['as-path'].split(" "))]
                    #print(ele)
                    if str(ele.type) == "R":
                        if 'as-path' and "prefix" in ele.fields:
                            IP = ele.fields["prefix"]
                            as_path[IP][peer] = hops
            history_rib[collector] = as_path

        ###extract AS-paths before event
        rib_before_incident = copy.deepcopy(history_rib)
        types = {"A", "W"}
        for collector in tqdm(self.collector_list):
            stream1 = pybgpstream.BGPStream(
                from_time=str(start-timedelta(hours=8)), until_time=str(start-timedelta(minutes=10)),
                collectors=[collector],
                record_type="updates",
                filter = f"prefix any {IP_prefix}"
            )
            
            for rec in tqdm(stream1.records()):
                for elem in rec:
                    if (str(elem.type) in types) and "prefix" in elem.fields:
                        IP = str(elem.fields["prefix"])
                        if str(elem.type) == "A" and "as-path" in elem.fields:
                            peer = str(elem.peer_asn)
                            hops = [k for k, g in groupby(elem.fields['as-path'].split(" "))]
                            rib_before_incident[collector][IP][peer] = hops
                            
                        if str(elem.type) == "W":
                            peer = str(elem.peer_asn)
                            rib_before_incident[collector][IP][peer] = []

        ###extract AS-paths after event
        rib_after_incident = copy.deepcopy(rib_before_incident)
        #collect information until 1min before event end or 10min after event start
        until = min(end-timedelta(minutes=1), start+timedelta(minutes=10))
        for collector in tqdm(self.collector_list):
            stream1 = pybgpstream.BGPStream(
                from_time=str(start-timedelta(minutes=10)), until_time=str(until),
                collectors=[collector],
                record_type="updates",
                filter = f"prefix any {IP_prefix}"
            )
            
            for rec in tqdm(stream1.records()):
                for elem in rec:
                    if (str(elem.type) in types) and "prefix" in elem.fields:
                        IP = str(elem.fields["prefix"])
                        if str(elem.type) == "A" and "as-path" in elem.fields:
                            peer = str(elem.peer_asn)
                            hops = [k for k, g in groupby(elem.fields['as-path'].split(" "))]
                            rib_after_incident[collector][IP][peer] = hops
                            
                        if str(elem.type) == "W":
                            peer = str(elem.peer_asn)
                            rib_after_incident[collector][IP][peer] = []

        return history_rib, rib_before_incident, rib_after_incident

    def AS_Path_AS(self, start_time, target_AS, end_time = None):
        '''
        Missing IP but provide target AS number and time to extract AS paths, end time is optional
        '''
        # convert start time to datetime object
        start = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        #convert end time to datetime object
        if end_time: #if end time is provided
            end = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        else: #default 1 day after start
            end = start + timedelta(days=1)


        ###extract history routing table
        history_rib = defaultdict(dict)
        target_IP_prefix = set([])
        for collector in tqdm(self.collector_list):
            #rcc collects rib every 8 hours, we pick the 2nd last checkpoint
            stream = pybgpstream.BGPStream(
                from_time=str(start-timedelta(hours=16)), until_time=str(start-timedelta(hours=8)),
                collectors=[collector],
                record_type="ribs",
                filter = f'aspath "{target_AS}$"' #collect all as path to target_AS
            )
            as_path = defaultdict(dict)

            for rec in tqdm(stream.records()):
                for ele in rec:
                    # Get the peer ASn
                    peer = str(ele.peer_asn)
                    hops = [k for k, g in groupby(ele.fields['as-path'].split(" "))]
                    #print(ele)
                    if str(ele.type) == "R":
                        if 'as-path' and "prefix" in ele.fields:
                            IP = ele.fields["prefix"]
                            target_IP_prefix.add(IP)
                            as_path[IP][peer] = hops
            history_rib[collector] = as_path

        ###extract AS-paths before event
        rib_before_incident = copy.deepcopy(history_rib)
        types = {"A", "W"}
        #construct filter by target IP prefix
        filter_string = f"prefix any"
        for ip_p in target_IP_prefix:
            filter_string += f" {ip_p}" 
        for collector in tqdm(self.collector_list):
            stream1 = pybgpstream.BGPStream(
                from_time=str(start-timedelta(hours=8)), until_time=str(start-timedelta(minutes=10)),
                collectors=[collector],
                record_type="updates",
                filter = filter_string
            )
            
            for rec in tqdm(stream1.records()):
                for elem in rec:
                    if (str(elem.type) in types) and "prefix" in elem.fields:
                        IP = str(elem.fields["prefix"])
                        if str(elem.type) == "A" and "as-path" in elem.fields:
                            peer = str(elem.peer_asn)
                            hops = [k for k, g in groupby(elem.fields['as-path'].split(" "))]
                            rib_before_incident[collector][IP][peer] = hops
                            
                        if str(elem.type) == "W":
                            peer = str(elem.peer_asn)
                            rib_before_incident[collector][IP][peer] = []

        ###extract AS-paths after event
        rib_after_incident = copy.deepcopy(rib_before_incident)
        #collect information until 1min before event end or 10min after event start
        until = min(end-timedelta(minutes=1), start+timedelta(minutes=10))
        for collector in tqdm(self.collector_list):
            stream1 = pybgpstream.BGPStream(
                from_time=str(start-timedelta(minutes=10)), until_time=str(until),
                collectors=[collector],
                record_type="updates",
                filter = filter_string
            )
            
            for rec in tqdm(stream1.records()):
                for elem in rec:
                    if (str(elem.type) in types) and "prefix" in elem.fields:
                        IP = str(elem.fields["prefix"])
                        if str(elem.type) == "A" and "as-path" in elem.fields:
                            peer = str(elem.peer_asn)
                            hops = [k for k, g in groupby(elem.fields['as-path'].split(" "))]
                            rib_after_incident[collector][IP][peer] = hops
                            
                        if str(elem.type) == "W":
                            peer = str(elem.peer_asn)
                            rib_after_incident[collector][IP][peer] = []

        return history_rib, rib_before_incident, rib_after_incident

    def generate_report(self, history_rib, rib_before_incident, rib_after_incident, time, IP="unknown", AS="unkonwn", Event_Type = "unknown"):
        '''
        provide history routing table, routing table before event, routing table after event, event time, IP or AS (must provide one)
        generate LLM explaination and report
        First generate N descriptions of changes in AS path before and after the event
        Second give N decisions of the event type based on the descriptions
        Third, use self-consistency machenism with N descriptions and N event type decisions generate final description and final event type
        prediction
        Finally, generate the report explaining the BGP anomaly event
        '''
        if IP != "unknown":
            event_type_list = [] #save n event type prediction
            description_list = [] #save n descriptions of the AS path changes
            for i in trange(5): #n=5
                #generate description of AS path changes before and after the event
                system_prompt = "You are an expert in Border Gateway Protocol. Given a set of AS paths to a specific IP prefix, \
                                    describe the changes in these paths before and after a time stamp. Try to answer the following questions:\n \
                                    Does the existing path from each peer to the target IP prefix change?\
                                    If it does, does the last AS (destination) change or not?\n \
                                    Is there any new AS path to a new sub-prefix introduced?\
                                    If there is, compare it to the existing path with the same peer, is there any difference? Does the last \
                                    AS (destination) change ot not?"
                user_prompt = f"{IP} is the target IP prefix. {time} is the time stamp. \n\
                                Here are the paths to this IP prefix and its sub-prefixes in history: {history_rib} \n \
                                Here are the paths to this IP prefix and its sub-prefixes before the time stamp: {rib_before_incident}. \n \
                                Here are the paths after the time stamp: {rib_after_incident}. \n \
                                All pathes are stored in a dictironary in a form of \
                                {{collector name: {{IP prefix: {{peer: [AS path from peer to the origin AS of IP prefix]}}}}}}. \
                                For example, in an AS path '97600:[97600, 12334, 54323, 2134]' 2134 is last and the destination AS.\
                                Now, describe the AS path changes."
                message = self.make_message(user_prompt=user_prompt, system_prompt=system_prompt)
                output_description = self.chat(messages=message, model=self.model)[0]
    
                #generate Event type prediction based on the description
                system_prompt_3 = "A BGP route leak often results in adding unexpected transit ASes without changing the \
                                    destination AS. In contrast, a BGP hijack typically leads to changing the destination AS in the AS path\
                                    and potentially redirecting traffic away from the legitimate owner. These consequence may reflect \
                                    in even just one AS path and in a sub-prefix.\n \
                                    Now I will provide you an analysis of AS path change before and after an event, you need to identify the\
                                    type of this event. Think step by step. Reply in one sentence.\n"
                user_prompt_3 = f"Analysis:{output_description}"
                message = self.make_message(user_prompt=user_prompt_3, system_prompt=system_prompt_3)
                output_event_type = self.chat(messages=message, model=self.model)[0]
                event_type_list.append(output_event_type)
                description_list.append(output_description)

            #generate final description and event type prediction that is in accordance with most of the descriptions and event types
            system_prompt_00 = f"Given a list of descriptions of the event type of the same event, identify the event type by choose the \
                                one in most descriptions. Output the event type and one sentence of explaination."
            user_prompt_00 = f"List of event type description {event_type_list}."
            message = self.make_message(user_prompt=user_prompt_00, system_prompt=system_prompt_00)
            output_event = self.chat(messages=message, model=self.model)[0]

            system_prompt_01 = f"Given a list of report of the AS path changes, generate one output report that is in accordance to the most\
                                report in the given list."
            user_prompt_01 = f"List of AS path change report {description_list}."
            message = self.make_message(user_prompt=user_prompt_01, system_prompt=system_prompt_01)
            output_change = self.chat(messages=message, model=self.model)[0]

            #Write report
            system_prompt_4 = "You are an expert in BGP network anomaly detection and explaination.\
                                Now I detect there is an anomaly event that happened at a certain time, \
                                but I don't know what happened exactly and need your help.\
                                I will provide you an analysis of the type of the event and a description of the change in AS paths\
                                before and after the event. I will also provide you the AS pathes collected by many collectors to the\
                                target IP prefix and its sub-prefixes before the anomaly event, after the anomaly event, \
                                and in the history for reference. Then you need to gather these information and write a report about \
                                this event, including time, anomaly type, related AS number and IP address to explain in detail about \
                                this event. If the data provided is not enough for you to identify\
                                the anomaly event, based on history data, list what necessary data is missing (i.e. the collectors that are\
                                missing)."
            user_prompt_4 = f"{IP} is the IP prefix we detected has a problem. {time} is the time that we detected the event start.\
                            {output_event} is the description about the event type. \n \
                            {output_change} is the description of the change in AS paths before and after the event. \n \
                            Here are the paths to this IP prefix in history: {history_rib} \n \
                            Here are the paths to this IP prefix before the event: {rib_before_incident}. \n \
                            Here are the paths after the event: {rib_after_incident}. \n \
                            All pathes are stored in a dictironary in a form of \
                            {{collector name: {{IP prefix: {{peer: [AS path from peer to IP prefix]}}}}}}. \
                            Now, write the BGP anomaly event report. List what necessary data is missing"
            message = self.make_message(user_prompt=user_prompt_4, system_prompt=system_prompt_4)
            output_report = self.chat(messages=message, model=self.model)[0]
            output_dict = {"raw_change": description_list,
                          "raw_event": event_type_list,
                          "final_change": output_change,
                          "final_event": output_event,
                          "report": output_report}
            
            
        elif AS != "unknown": #not using
            #IP prefix not available but AS number is available
            system_prompt = "You are an expert in BGP network anomaly detection and explaination.\
                            Now we detect there is an anomaly event that happened at a certain time, \
                            but we don't know what happened exactly and need your help. \
                            We will provide you the AS pathes collected by many collectors to the IP prefixes of a target AS\
                            before the anomaly event and after. We will also provide AS pathes to those IP prefixes in the history. \
                            Also we will provide you the time. You need to explain what happened and what kind of anomaly event this is. \
                            Then you need to write a report about this event, including time, anomaly type, \
                            related AS number and IP address. If the data provided is not enough for you to write the report, please \
                            explain what data is missing."
            user_prompt = f"AS{AS} is the autonomous system we detected has a problem. {time} is the time that we detected the event start.\
                            Here are the paths to this AS in history: {history_rib} \n \
                            Here are the paths to this AS before the event: {rib_before_incident}. \n \
                            Here are the paths after the event: {rib_after_incident}. \n \
                            All pathes are stored in a dictironary in a form of \
                            {{collector name: {{IP prefix: {{peer: [AS path from peer to IP prefix]}}}}}}. Now, write the report."
            message = self.make_message(user_prompt=user_prompt, system_prompt=system_prompt)
            output_report = self.chat(messages=message, model=self.model)[0]
        else:
            raise("Must provide at least one IP or AS!")
        return output_report, output_dict
