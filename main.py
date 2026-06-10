from pathlib import Path as FilePath
from pydantic import BaseModel, Field, computed_field
from fastapi.responses import JSONResponse
from typing import Annotated, Literal, Optional
import json

from fastapi import FastAPI, Path, HTTPException, Query

app = FastAPI()

DATA_FILE = "/content/fastapi_campux/patients.json"


class Patient(BaseModel):
    id: Annotated[
        str,
        Field(..., description="id of the patient", examples=["P001"])
    ]
    name: Annotated[
        str,
        Field(..., description="give the name of the patient")
    ]
    city: Annotated[
        str,
        Field(..., description="city of the patient")
    ]
    age: Annotated[
        int,
        Field(..., gt=0, lt=120, description="Age of the patient")
    ]
    gender: Annotated[
        Literal["male", "female", "other"],
        Field(..., description="gender of the patient")
    ]
    height: Annotated[
        float,
        Field(..., gt=0, description="height of the patient")
    ]
    weight: Annotated[
        float,
        Field(..., gt=0, description="weight of the patient")
    ]

    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight / (self.height ** 2), 2)
        return bmi

    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "underweight"
        elif 18.5 <= self.bmi <= 24.9:
            return "normal"
        elif 25 <= self.bmi <= 29.9:
            return "overweight"
        else:
            return "obese"






class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None,gt=0)]
    gender: Annotated[Optional[Literal["male", "female"]], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight:Annotated[Optional[float], Field(default=None, gt=0)]


def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


@app.get("/")
def hello():
    return {"message": "Patient Management System"}


@app.get("/view")
def view():
    return load_data()


@app.get("/patient/{patient_id}")
def view_patient(
    patient_id: str = Path(
        ..., description="Id of the patient", examples=["P001"]
    )
):
    data = load_data()

    if patient_id in data:
        return data[patient_id]

    raise HTTPException(status_code=404, detail="Patient not found")


@app.get("/sort")
def sort(
    sort_by: str = Query(
        ..., description="Field to sort by height, weight or bmi"
    ),
    order: str = Query(
        "asc", description="sort in asc or desc order"
    ),
):
    valid_fields = ["height", "weight", "bmi"]

    if sort_by not in valid_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid field select from {valid_fields}",
        )

    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid order select from asc or desc",
        )

    data = load_data()

    sort_order = False if order == "asc" else True

    sorted_data = sorted(
        data.values(),
        key=lambda x: x.get(sort_by, 0),
        reverse=sort_order,
    )

    return sorted_data


@app.post("/create")
def create_patient(patient: Patient):
    data = load_data()

    if patient.id in data:
        raise HTTPException(
            status_code=400,
            detail="patient already exists",
        )

    data[patient.id] = patient.model_dump(exclude=["id"])

    save_data(data)

    return JSONResponse(
        content={"message": "patient created"},
        status_code=201,
    )

@app.put('/edit/{patient_id}')
def update_patient(patient_id:str,patient_update:PatientUpdate):

    data =load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404,detail='patient not found')
    
    existing_patient_info = data[patient_id]

    update_patient_info=patient_update.model_dump(exclude_unset=True)

    for key, value in update_patient_info.items():
        existing_patient_info[key]=value

    existing_patient_info['id']=patient_id
    patient_pydandic_obj = Patient(** existing_patient_info)

    existing_patient_info= patient_pydandic_obj.model_dump(exclude={'id'})

    data[patient_id]= existing_patient_info

    save_data(data)

    return JSONResponse(status_code=200, content={'message':'patient updated'})
    
@app.delete('/delete/{patient_id}')
def delete_pateint(patient_id:str):

        data=load_data()
        if patient_id not in data:
            raise HTTPException(status_code=404,detail='patient not found')
        del data[patient_id]

        save_data(data)
        
        return JSONResponse(status_code=200, content={'message':'patient deleted'})

    


