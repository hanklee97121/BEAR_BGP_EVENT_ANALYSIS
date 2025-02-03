# **BEAR: BGP Event Analysis and Reporting**  

**BEAR** is a framework for generating comprehensive reports on **BGP anomaly events** using **large language models (LLMs)**. This repository contains the implementation of **BEAR**, including support for different LLMs and handling scenarios with **limited data availability**. Also, this repository includes implentation of **Synthetic BGP Anomaly Event Data Generation**.

## **Table of Contents**  
- [Installation](#installation)  
- [Usage](#usage)  
- [Files and Structure](#files-and-structure)  
- [Examples](#examples)  
- [Switching to a Different LLM](#switching-to-a-different-llm)  
- [License](#license)  

## **Installation**  
To use **BEAR**, clone this repository and install the required dependencies:  
```bash
git clone https://github.com/your_username/BEAR.git  
cd BEAR  
sudo apt-get install bgpstream  
pip install -r requirements.txt  
```  

## **Usage**  

Run **BEAR** to generate reports on our dataset:  
```python
import pandas as pd
from BEAR import BEAR

data = 'Data/BGP_explain_data.csv'
rcc_collector_lists = ["rrc00", "rrc01", "rrc03", "rrc04", "rrc05", "rrc06", "rrc07", "rrc10", "rrc11", "rrc12", "rrc10", "rrc11",
                      "rrc12", "rrc13", "rrc14", "rrc15", "rrc16", "rrc17", "rrc18", "rrc19", "rrc20", "rrc21", "rrc22", "rrc23",
                      "rrc24", "rrc25", "rrc26"] 
generator = BEAR(collector_list=rcc_collector_lists, model = "gpt-4o", project = "rcc", save_path = "e_8/", read_path = "e_1/")
```

Run **BEAR** to generate report for a **BGP Anomaly Event**:
```python
generator.generate_single_event(self, start_time, file_save_prefix="", IP=None, AS=None, end_time=None, Event_Type=None)
```
Specify necessary event related parameters:
- `start_time`: event start time
- `IP`: victim IP prefix
- `end_time`: event end time, optional

Other parameters (`AS`, `Event_Type`) are not used in current report generator and can be ignored. All example usage codes and comments can be find in `BEAR_experiment.py` and `BEAR_experiment.ipynb`

Run **BEAR** for limited data scenarios:  

The main difference between run **BEAR** on full data and limited data scenario is you need to use `BEAR_few_collector` instead of `BEAR` and specify `n_collector` (number of collectors) parameter. Example usage codes are in `BEAR_few_collector_experiment.ipynb`

## **Files and Structure**  

### **Core Components**  
- **`LLM_Module.py`** – Handles all LLM-specific operations. To switch to a different LLM, modify this file.  
- **`BEAR.py`** – Main script implementing the **BEAR** method for generating reports on **BGP anomaly events**.  
- **`BEAR_few_collector.py`** – A variation of **BEAR** designed to work with **limited data availability**.  

### **Experiments and Examples**  
- **`BEAR_experiment.py`** – Example script demonstrating how to use **BEAR** to generate reports.  
- **`BEAR_experiment.ipynb`** – Jupyter Notebook version of **BEAR_experiment.py** for interactive use.  
- **`BEAR_few_collector_experiment.ipynb`** – Example notebook for generating reports when **data is limited**.  

### **Data and Experiments**
- **`Data`** - Folder storing informations of BGP anomaly events in our experiment.
    - `BGP_explain_data.csv` contians information of both real and synthetic BGP anomaly events.
- **`Experiment`** - Folder storing experimental results of **BEAR**
    - `e_1` contains BGP data for all events and reports generate by naive baseline method (directly feeding data to LLM)
    - `e_8` contains reports generate by **BEAR**

### **Synthetic BGP Event Data**
- `Synthetic_BGP_Event_Data` - Folder containing codes and comments for BGP anomaly event data generation.

## **Switching to a Different LLM**  
To use a different **LLM**, modify the **`LLM_Module.py`** file. Update the model API, parameters, or fine-tuning instructions as needed to integrate a new LLM.  

## **License**  
This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.  

