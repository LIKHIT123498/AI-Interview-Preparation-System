import axios from 'axios';

const API_BASE_URL="http://localhost:8000/api/v1";

export const uploadResumeAndJD=async(userId,jobDescription,file)=>{
    const formData=new FormData();
    formData.append("user_id",userId);
    formData.append("job_description",jobDescription);
    formData.append("file",file);

    const response=await axios.post(`${API_BASE_URL}/analyze-resume`,formData,{
    headers:{
        "Content-Type":"multipart/form-data",
    },
    });
    return response.data;
}