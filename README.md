Dashbirth - [Data Shack 2024](https://sites.google.com/view/datashack-harvard-polimi/data-shack-2024)
==============================

**Team Members**
Yuqin (Bailey) Bai, Luca Bottani, Sara Merengo, and Li Yao

**[Project Objectives](https://sites.google.com/view/datashack-harvard-polimi/data-shack-2024#h.ejfv8fmb4s2f)**
This project proposes to utilize advanced language models to analyze postpartum surveys completed by thousands of mothers. The aim is to derive actionable insights that can further enhance the [TeamBirth](https://www.ariadnelabs.org/delivery-decisions-initiative/teambirth/) program, particularly focusing on reducing maternal mortality rates and addressing mistreatment and disparities in maternal health.
* To deploy language models in summarizing and analyzing postpartum surveys from mothers who have participated in the TeamBirth program.
* To identify areas where TeamBirth can be refined to further reduce maternal mortality and mistreatment.
* To develop targeted interventions based on the insights gleaned from the survey analysis.

## Proposed Solution
An interactive dashboard website that TeamBirth can use in order to visualize the data and share it to the hospitals.

### Frontend Simple Container
* Build & run container by running the commands with the absolute path to your data folder
    ```
    cd src/frontend_simple

    docker build -t frontend_simple -f Dockerfile .
    docker run -d -p 5001:5000 -v </absolute/path/to/your/data>:/data frontend_simple
    ```
- Go to page `http://localhost:5001/`


<img src="images/Technical_Arch.jpg"  width="800">

### Vector Database Container

### Retrival Container

### Large Language Model Container

### API Service Container

### Frontend Container

## Docker Cleanup
Make sure we do not have any running containers and clear up an unused images.
* Run `docker container ls`
* Stop any container that is running
* Run `docker system prune`
* Run `docker image ls`