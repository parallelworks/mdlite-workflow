import paramUtils
import argparse
import data_IO

parser = argparse.ArgumentParser(
    description='Generate the caseList file which lists the parameter names and values '
    'for each simulation case per line by expanding the parameters in the sweep.run file.')

parser.add_argument("sweepRunFile",
                    help="The sweepRunFile file contains parameter names and their values.")

parser.add_argument("caseListFile",
                    help="The output file of this function. The address of the file listing "
                         "the parameter names and values for each simulation case per line.")

parser.add_argument("--SR_valueDelimiter", default='_',
                    help='The delimiter to separate multiple values in a list in '
                         '<sweepRunFile> (default:"_")')

parser.add_argument("--SR_paramValueDelimiter", default=';',
                    help='The delimiter between a parameter name and its value in '
                         '<sweepRunFile> (default:";")')

parser.add_argument("--SR_paramsDelimiter", default='|',
                    help='The delimiter to separate parameter/value pairs from each other in '
                         '<sweepRunFile> (default:"|")')

parser.add_argument("--withParamTag", dest='withParamTag', action='store_true',
                    help='If set, a tag can be specified between the parameter name and '
                         'its value (delimited by SR_namesDelimiter). This is the default.')

parser.add_argument("--noParamTag", dest='withParamTag', action='store_false',
                    help='If set, no tag is expected between the parameter name and its value.')


parser.add_argument("--CL_paramValueDelimiter", default=',',
                    help='The delimiter between a parameter name and its value in '
                         '<casesListFile> (default:",")')

parser.set_defaults(withParamTag=True)


args = parser.parse_args()
casesListFile = args.caseListFile
paramsFile = args.sweepRunFile
SR_valsdelimiter = data_IO.correctDelimiterInputStrs(args.SR_valueDelimiter)
SR_paramsDelimiter = data_IO.correctDelimiterInputStrs(args.SR_paramsDelimiter)
SR_withParamTag = args.withParamTag
SR_paramValueDelimiter = data_IO.correctDelimiterInputStrs(args.SR_paramValueDelimiter)
CL_paramValueDelimiter = data_IO.correctDelimiterInputStrs(args.CL_paramValueDelimiter)

cases = paramUtils.readCases(paramsFile,
                             valsdelimiter=SR_valsdelimiter,
                             paramsdelimiter=SR_paramsDelimiter,
                             withParamType=SR_withParamTag,
                             namesdelimiter=SR_paramValueDelimiter)[0]

print("Generated "+str(len(cases))+" Cases")

caselist = paramUtils.generate_caselist(cases, pnameValDelimiter=CL_paramValueDelimiter)

casel = "\n".join(caselist)

f = open(casesListFile, "w")
f.write(casel)
f.close()
