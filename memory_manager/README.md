The memory-allocation table is updated at every refresh of the page by reading at `http://localhost:8000/simulate/shared_memory/read`(shared_memory) looking for data written by the process_scheduler to the shared memory.
The data read is updated within the table accordingly.
