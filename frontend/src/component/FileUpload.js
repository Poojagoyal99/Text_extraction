
import React, { useState } from "react";
import axios from "axios";

const FileUpload = () => {
  const [file, setFile] = useState(null); 
  const [responseText, setResponseText] = useState(""); 
  const handleChange = (e) => {
    setFile(e.target.files[0]); 
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file first");
      return;
    }

    const formData = new FormData();
    formData.append("file", file); 

    try {
      const res = await axios.post('http://127.0.0.1:8000/api/upload/', formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setResponseText(res.data.text || "Uploaded successfully!"); 
    } catch (err) {
      console.error(err);
      alert("Error uploading file");
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>Upload a File</h2>
      <input type="file" onChange={handleChange} />
      <button onClick={handleUpload}>Upload</button>

      {responseText && (
        <div>
          <h3>Extracted Text:</h3>
          <pre>{responseText}</pre>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
