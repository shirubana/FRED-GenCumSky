function [] = convertGenCumSky2FRED(GenCum_File, GenCum_FRED_File)
% Convert GENCUMULSKY Output .CAL Files to FRED .txt files
% Example:
%   GenCum_File='Richmondcumulative.cal';
%   GenCum_FRED_File='GenCumSky_FRED_Richmond.txt';
%   convertGenCumSky2FRED(GenCum_File, GenCum_FRED_File)

    fprintf('Reading File %s\n', GenCum_File)
    fprintf('Writing to File %s\n', GenCum_FRED_File)

    fileID = fopen(GenCum_File,'r');
    fileIDSave = fopen(GenCum_FRED_File,'w');

    Intro = textscan(fileID,'%s',4,'Delimiter','\n');
    trash = textscan(fileID,'%s',1,'Delimiter','\n');

    row0header = textscan(fileID,'%s',1,'Delimiter','\n');
    row0valscan = textscan(fileID,'    %f,');     % Read the numeric value 
    row0val = row0valscan{1};
    row0 = row0val(1:30,1);

    trash = textscan(fileID,'%s',2,'Delimiter','\n');

    row1header = textscan(fileID,'%s',1,'Delimiter','\n');
    row1valscan = textscan(fileID,'    %f,');     % Read the numeric value 
    row1val = row1valscan{1};
    row1 = row1val(1:30,1);

    trash = textscan(fileID,'%s',2,'Delimiter','\n');

    row2header = textscan(fileID,'%s',1,'Delimiter','\n');
    row2valscan = textscan(fileID,'    %f,');     % Read the numeric value 
    row2val = row2valscan{1};
    row2 = row2val(1:24,1);

    trash = textscan(fileID,'%s',2,'Delimiter','\n');

    row3header = textscan(fileID,'%s',1,'Delimiter','\n');
    row3valscan = textscan(fileID,'    %f,');     % Read the numeric value 
    row3val = row3valscan{1};
    row3 = row3val(1:24,1);

    trash = textscan(fileID,'%s',2,'Delimiter','\n');

    row4header = textscan(fileID,'%s',1,'Delimiter','\n');
    row4valscan = textscan(fileID,'    %f,');     % Read the numeric value 
    row4val = row4valscan{1};
    row4 = row4val(1:18,1);

    trash = textscan(fileID,'%s',2,'Delimiter','\n');

    row5header = textscan(fileID,'%s',1,'Delimiter','\n');
    row5valscan = textscan(fileID,'    %f,');     % Read the numeric value 
    row5val = row5valscan{1};
    row5 = row5val(1:12,1);

    trash = textscan(fileID,'%s',2,'Delimiter','\n');

    row6header = textscan(fileID,'%s',1,'Delimiter','\n');
    row6valscan = textscan(fileID,'    %f,');     % Read the numeric value 
    row6val = row6valscan{1};
    row6 = row6val(1:6,1);

    trash = textscan(fileID,'%s',2,'Delimiter','\n');

    row7val = textscan(fileID,'row7=if(alt-84,%f,0);');     % Read the numeric value 
    row7 = row7val{1};                             % Specify that this is the 

    clear row0valscan row0val row1val row1valscan row2val row2valscan row3val 
    clear row3valscan row4val row4valscan row5val row5valscan row6val row6valscan
    clear trash

    sky=[row0;row1;row2;row3;row4;row5;row6;row7];

    for foo=1:1:145
        fprintf(fileIDSave,'%8.6f\r\n',sky(foo));
    end

    fprintf(fileIDSave,'%8.6f\r\n',min(sky));
    fprintf(fileIDSave,'%8.6f',max(sky));


    fclose(fileIDSave);

    fprintf('Finished Conversion.\n\n')

end


