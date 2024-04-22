Dashbirth - [Data Shack 2024](https://sites.google.com/view/datashack-harvard-polimi/data-shack-2024)
==============================

**Team Members**
Yuqin (Bailey) Bai, Luca Bottani, Sara Merengo, and Li Yao

**[Project Objectives](https://sites.google.com/view/datashack-harvard-polimi/data-shack-2024#h.ejfv8fmb4s2f)**
This project proposes to utilize advanced language models to analyze postpartum surveys completed by thousands of mothers. The aim is to derive actionable insights that can further enhance the [TeamBirth](https://www.ariadnelabs.org/delivery-decisions-initiative/teambirth/) program, particularly focusing on reducing maternal mortality rates and addressing mistreatment and disparities in maternal health.
* To deploy language models in summarizing and analyzing postpartum surveys from mothers who have participated in the TeamBirth program.
* To identify areas where TeamBirth can be refined to further reduce maternal mortality and mistreatment.
* To develop targeted interventions based on the insights gleaned from the survey analysis.

## Patient Data Privacy
Following the Ethical Principles & Guidelines for Research Involving Human Subjects, maintaining the confidentiality of patient data is paramount. In our efforts to utilize advanced language models for analyzing surveys, we are committed to ensuring that no patient-related data is exposed to external APIs, including ChatGPT. We understand the risks associated with data privacy and have implemented robust solutions to safeguard information.

To address different data storage and usage needs while ensuring data privacy, we offer the following solutions:

### Local Hosting
For a straightforward setup, we provide the option to locally host the dashboard. This setup includes all modules except for the open feedback and chatbot features.

It is highly suggested to store any patient-related data in a dedicated folder outside the Git repository. This practice prevents the accidental upload of confidential data to version control systems where it could be exposed to unauthorized access.

**Setup Instructions**
1. Ensure you have Docker installed on your system.
2. Have your data stored securely as suggested, outside of your project’s Git repository.
3. Follow the instructions in our [Frontend Simple Container Setup](#frontend-simple-container) to deploy locally.

### Advanced Deployment with Google Cloud Platform
For enhanced security and control, we recommend deploying our solution using the Google Cloud Platform (GCP). This approach utilizes Google Cloud's robust security measures, including isolated storage and controlled access.

Why Choose Google Cloud Storage (GCS) and GCP Virtual Machine (VM)?
* **GCS buckets** offer advanced security features that make it a preferable choice over options like Google Drive. GCS provides fine-grained access controls and is designed for high durability and availability.
* GCP **VM instances** provide a secure environment for hosting our custom language models, eliminating the risks associated with using external APIs.



## Proposed Solution
An interactive dashboard website that TeamBirth can use in order to visualize the data and share it to the hospitals.

### Prerequisites
* Have Docker installed

### Frontend Simple Container
* Build & run container by running the commands with the absolute path to your data folder
    ```
    cd src/frontend_simple

    docker build -t frontend_simple -f Dockerfile .
    docker run -d -p 5001:5000 -v </absolute/path/to/your/data>:/data frontend_simple
    ```
- Go to page `http://localhost:5001/`


---
<img src="images/Technical_Arch.jpg"  width="800">

### Vector Database Container

### Retrival Container

### Large Language Model Container
This container serves a Large language model (LLM) on GCP VM. We choose a 












### API Service Container


## Docker Cleanup
Make sure we do not have any running containers and clear up an unused images.
* Run `docker container ls`
* Stop any container that is running
* Run `docker system prune`
* Run `docker image ls`