# Amazon_BGP_LLM_Reasoning
Use LLM to explain a BGP anomaly event and create a report

Net_Graph_2.ipynb:
  Code to extract all AS paths related to a BGP hijack event from one collector. Code for this example https://docs.google.com/document/d/1KmQJd7EXWpwsN1WhqhZneVP5T7f14_kJ/edit

Net_Graph_2.ipynb:
  Code to extract all AS paths related to an event from all collector (either IP prefix available or not).

LLM_BGP_Anomaly_Explaination.ipynb:
  Code of the actual framework that takes events' data and output reports

LLM_BGP_Anomaly_Explaination_few_collector.ipynb:
  Code of the framework using partial data

LLM_BGP_Anomaly_Explaination_multi_step_multi_agent.ipynb:
  Code of the framework with multi-step and multi-agent to generate BGP event report.

Data/
  Event data saved in this directory
  BGP_explain_data.csv: csv file record BGP events
  BGP_explain_data_xx.xlsx: since csv doesn't support hyperlink, we save another data file in xlsx with hyperlink

Experiments/
  experiment results saved in this directory
  Experiment_Detail.xlsx: detailed config information for each experiment
