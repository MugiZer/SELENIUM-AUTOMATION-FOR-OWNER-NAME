import FileUpload from "@/components/FileUpload";

const Upload = () => {
  return (
    <div className="min-h-screen bg-background p-4">
      <div className="max-w-2xl mx-auto mt-20">
        <h1 className="text-2xl font-bold mb-6 text-center">Property Data Processor</h1>
        <FileUpload />
      </div>
    </div>
  );
};

export default Upload;
