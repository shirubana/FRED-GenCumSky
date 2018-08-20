function [] = convert1DArraytoFREDInputTextFile(arrayvar, FRED_Input_TextFile)
% Generate a 1 column array of values to be read on FRED into a
% 1-dimensional array value.
% Example:
%   arrayvar=[280, 281, 282,..... 3999, 4000];
%   FRED_Input_TextFile='2002_Wavelengths_from_TMY3.txt';
%   convert1DArraytoFREDInputTextFile(arrayvar, FRED_Input_TextFile)

    fprintf('Writing to File %s\n', FRED_Input_TextFile)

    fileIDSave = fopen(FRED_Input_TextFile,'w');

    for foo=1:1:length(arrayvar)
        fprintf(fileIDSave,'%0.1f\r\n',arrayvar(foo));
    end

    fclose(fileIDSave);
    fprintf('Finished Saving File.\n\n')


end




