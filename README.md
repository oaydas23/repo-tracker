The following program is for the purpose of organization with regard to repository commits and gradle. 

Grade still to be worked on, but build.gradle demonstrates how to post from gradle to flask...

To run on Docker input the following code in terminal

1. docker image build -t repo-tracker .
2. docker run -dp 5000:5000 --mount type=volume,src=todo-db,target=/app/data repo-tracker
