%6/24/2018
%SPIE Paper GenCumSky all patches values for all TMY3
% Going from Python --> GenCumSky .Cal files for each hour in TMY3, to 
% a single file that has all patches information in xlsx for the TMY3.
% Not very organized, but that's what it is.
% Silvana Ayala

%% Go from .Cal to .Txt
for i=8444:1:8760
    GenCum_File=strcat('C:\Users\Psl\Documents\RadianceScenes\Test3\cumulative_',num2str(i),'.cal');
    GenCum_FRED_File=strcat('C:\Users\Psl\Documents\RadianceScenes\Test3\cumulative_',num2str(i),'.txt');
    convertGenCumSky2FRED(GenCum_File, GenCum_FRED_File)
end

%% Go from .txt to One single Matrix in Matlab (apptly named "all")

all=[]
for foo=1:1:8760
    filetitle=strcat('C:\Users\Psl\Documents\RadianceScenes\Test3\cumulative_',num2str(foo),'.txt');
    A = textread(filetitle)';
    all = [all;A]; 
end

%% Find Max, Min, Patch where Max occurs, and save to Excel with headers
[B, BI]=max(all,[],2);
C=min(all,[],2);
all=[all,B,C,BI]; % joining max and min to ALL matrix.

% Creating Headers
F=[]
for i=1:1:145
    F=[F,{strcat('Patch ', num2str(i))}]
end
F=[F,'Max','Min','Max_Index_Patch']

% Saving
filesave='C:\Users\Psl\Documents\RadianceScenes\Test3\cumulative_ALL_Tucson.xlsx'
xlswrite(filesave,F,'Sheet1','A1')        
xlswrite(filesave,all,'Sheet1','A2')   