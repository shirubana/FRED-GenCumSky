function smartsRunbyTMY3(filesave, MODE, TMY3file)
    % function smartsRunDaybyHour(filesave, MODE, year, month, day, LATIT, LONGIT)
    % IMPORTAT Note: RUN OUTSIDE OF DROPBOX OR IT WILL CRASH.
    % Function that writes an excel with all hours in given day and the spectra
    % associated with mode selected
    % This takes approx. 25 mins to run for a whole TMY file and generates
    % a 93M excel file (Dell I7-core)
    %
    % Inputs:
    %    filesave - str with folderURL\filename where to save the file
    %    MODE = str. Examples:
    %      '2' Direct normal irradiance W m-2
    %      '3' Diffuse horizontal irradiance W m-2    
    %    TMY3file - str with folderURL\filename of the TMY3 file (.csv)

    % Output:
    %   Excel file with Columns: Month | Day | Hour | 2004 Wavelengths Spectra
    %   
    %   (The idea is that since it's reading the TMY3, it can also save
    %   all values of interest if desired just modifying this function).
    % Example USE:
    %       smartsRunbyTMY3('OUTPUT\Tucson_TMY3_Direct_Spectra.xlsx','2','722740.CSV') %
    %           
    %
    % Silvana Ayala (c) 2018

    warning('off', 'MATLAB:DELETE:FileNotFound')
    fprintf('CALL SMARTS FOR TMY3 Data, v 1.0 by Silvana \n *************************** \n\n')
    Notitle=1; % Used to save wavelengths for title of excel sheet only once.
    E_array=[];

    % Reading TMY3 using PVLib Matlab version
    % (Note that there was a modification on code to be able to read
    % headers
    % https://github.com/sandialabs/MATLAB_PV_LIB/blob/master/pvl_readtmy3.m
    TMYData = pvl_readtmy3(TMY3file);
    B=datetime(TMYData.DateString(:), 'InputFormat', 'MM/dd/yyyy');
    [year,month,day]=ymd(B);
    C=datetime(TMYData.TimeString(:), 'InputFormat', 'HH:mm');
    [hour,minute]=hms(C);
    hour(isnan(hour))=24;
    minute(isnan(minute))=0;
    Latitude = TMYData.SiteLatitude;
    Longitude = TMYData.SiteLongitude;
    LATIT=strcat((num2str(round(Latitude))),'.');  % Format Required for Latitude by SMARTS
    
    for (ct=1:1:length(TMYData.DateString))
                % Call to SMARTS HERE.
                % DON'T RUN WHILE IN DROPBOX OR WILL CRASH
                E_theor=smartsRun(MODE,num2str(year(ct)),num2str(month(ct)), num2str(day(ct)), num2str(hour(ct)),LATIT,num2str(Longitude));
                E_row=[];

                % Saving in row format.
                % If irradiance data = 0, still saves 0's for that time.
                if size(E_theor,1)==1
                    E_row=[month(ct),day(ct),hour(ct), zeros(1,2003)];
                else
                    E_row=[month(ct),day(ct),hour(ct), E_theor(:,2)'];
                    if (Notitle)
                        title_rows=[{'Month'},{'Day'},{'Hour'},num2cell(E_theor(:,1)')];
                        title_rows(4)={'wavelength (nm)--> '};
                        Notitle=0;
                    end
                end

                % After putting all irradiance data in row format, adds it
                % to the main array. Arrays are saved one excell per day.
                E_array=[E_array;E_row];
                % formattedPlot(E_theor); 
    end
    
        fprintf('Saving Spectra Data for TMY3 in Excell... \n')
        xlswrite(filesave,title_rows,'Sheet1','A1')        
        xlswrite(filesave,E_array,'Sheet1','A2')        

end
