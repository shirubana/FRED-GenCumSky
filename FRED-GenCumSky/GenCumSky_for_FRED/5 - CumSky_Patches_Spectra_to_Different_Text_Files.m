% 1 - 8 AM June 21

for fooct=8:1:17
    num  = xlsread('D:\Dropbox\KOSTUK\sayala\SPIE2018\GenCumSky_Spectra_Dec21_reduced.xlsx',fooct-7);

    for foo=2:1:2003
        wavvalues = num(2:end,foo);
        wavtitle = num(1,foo);

        fileIDSave = fopen(['D:\Dropbox\KOSTUK\sayala\SPIE2018\Dec21_',num2str(fooct),'_PatchesEmmitbyWavelength\wav_',num2str(wavtitle),'.txt'],'w');

        for i=1:1:145
            fprintf(fileIDSave,'%0.10f\r\n', wavvalues(i));
        end

        fprintf(fileIDSave,'%0.10f\r\n', min(wavvalues));
        fprintf(fileIDSave,'%0.10f', max(wavvalues));
        fclose(fileIDSave);

    end
    
end
