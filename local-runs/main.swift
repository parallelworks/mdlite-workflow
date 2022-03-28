# MD-lite parameter sweep

type file;
############################################
# ------ INPUT / OUTPUT DEFINITIONS -------#
############################################

# workflow inputs
# comment this line out when running under dakota
file params         <arg("paramFile","params.run")>;

# other inputs
string outdir       = "results/"; # Directory where the outputs are saved
string casedir      = strcat(outdir,"case"); # Directory where the outputs for each case are saved

# add models - SWIFT DOES IT THIS WAY
file[] mdlite       <Ext;exec="utils/mapper.sh",root="models/mdlite">;
file[] cray         <Ext;exec="utils/mapper.sh",root="models/c-ray">;
file[] mexdex       <Ext;exec="utils/mapper.sh",root="models/mexdex">;

# PARSL DOES IT THIS WAY:
files_to_stage = [Path("models/mdlite"),Path("models/c-ray"),Path("models/mexdex")]

@bash_app
my_parsl_app(inputs=files_to_stage, outputs=[]):
	# Now you can access mdlite, c-ray, and mexdex


Path.py is in the ocean_parcels_demo.  Include it in the MDLite workflow folder.


# workflow outputs
file outhtml        <arg("html","results/output.html")>;
file outcsv         <arg("csv","results/output.csv")>;
string path         = toString(@java("java.lang.System","getProperty","user.dir"));

##############################
# ---- APP DEFINITIONS ----- #
##############################
# Combines the parameters in params.run to produce all the cases
@bash_app(inputs=[],outputs=[]):
	python prepinputs.py

app (file out) prepInputs (file params, file s[])
{
  python "models/mexdex/prepinputs.py" @params @out;
}

# generate parametric mesh
app (file trjOut, file metricOut, file o, file e) runMD (string caseParams, file[] mdlite) {
  bash_hp "models/mdlite/runMD.sh" caseParams @metricOut @trjOut stdout=@o stderr=@e;
}

# render the trajectories
app (file pngOut) renderFrame (int ri, file trjOut, file[] cray) {
  bash "models/c-ray/renderframe" @trjOut @pngOut ri;
}

# convert to animation
app (file o) convert (file s[])
{
  convert "-delay" 10 filenames(s) @o;
}

# Produces the html file for visualization and organization of results
app (file outcsv, file outhtml, file o, file e) postProcess (file[] t, string rpath, file caselist, file[] mexdex) {
  bash "models/mexdex/postprocess.sh" filename(outcsv) filename(outhtml) rpath stdout=@o stderr=@e;
}

######################
# ---- WORKFLOW ---- #
######################

file caselist <"cases.list">;

# comment this line out when running under dakota
caselist = prepInputs(params, mexdex);

# In built function to read each line in caselist into an array of strings
string[] cases = readData(caselist);

tracef("\n%i Cases in Simulation\n\n",length(cases));

# For each case run through the models
file[] metrics;
foreach c,caseIndex in cases{

  # RUN MD-LITE
  file trjOut     <strcat("results/case_",caseIndex,"/trj.out")>;
  file metricOut  <strcat("results/case_",caseIndex,"/metric.out")>;
  file mo 	      <strcat("results/logs/case_",caseIndex,"/mdlite.out")>;
  file me 	      <strcat("results/logs/case_",caseIndex,"/mdlite.err")>;
  (trjOut, metricOut, mo, me) = runMD(c, mdlite);
  metrics[caseIndex] = metricOut;

  string[] m = readData(metricOut);
  int trsnaps = toInt(m[0]);

  # GENERATE FRAMES
  file frames[] <simple_mapper; prefix=strcat("results/case_",caseIndex,"/png/"), suffix=".png">;
  foreach i in [0:trsnaps-1] {
    frames[i] = renderFrame(i,trjOut,cray);
  }
  file gifOut <strcat("results/case_",caseIndex,"/mdlite.gif")>;
  gifOut = convert(frames);
}

# For all cases creates a csv list and html file for visualization and organization of results
file spout <"logs/post.out">;
file sperr <"logs/post.err">;
(outcsv,outhtml,spout,sperr) = postProcess(metrics,path,caselist,mexdex);
