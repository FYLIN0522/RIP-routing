sourceNodes = input("Source nodes")
transitNodes = input("Transit nodes")
destNodes= input("Destination nodes")

X = [i for i in range(1, int(sourceNodes) + 1)]
Y = [i for i in range(1, int(transitNodes) + 1)]
Z = [i for i in range(1, int(destNodes) + 1)]


def demand_volumes_constraint():
    demandflow = ""
    for sourceNode in X:
        for destNode in Z:
            equation = ""
            for transitNode in Y:
                equation += ("x{}{}{} + ".format(sourceNode, transitNode, destNode))

            h_ij = sourceNode + destNode
            equation = equation[:-2] + "= " + str(h_ij) + "\n" 
            demandflow += equation

    demandflow += "\n"
    return demandflow



def ST_capacity_constraint():
    capp = ""
    for sourceNode in X:
        for transitNode in Y:
            equation = ""
            for destNode in Z:
                equation += ("x{}{}{} + ".format(sourceNode, transitNode, destNode))

            i = sourceNode
            k = transitNode
            C_ik = "c" + str(i) + str(k)
            equation = equation[:-2] + "- r * " + C_ik + " <= 0" + "\n" 
            capp += equation

    capp += "\n"
    return capp



def TD_capacity_constraint():
    capp = ""
    for transitNode in Y:
        for destNode in Z:
            equation = ""
            for sourceNode in X:
                equation += ("x{}{}{} + ".format(sourceNode, transitNode, destNode))

            k = transitNode
            j = destNode
            D_kj = "d" + str(k) + str(j)
            equation = equation[:-2] + "- r * " + D_kj + " <= 0" + "\n" 
            capp += equation
            
    capp += "\n"
    return capp



def indicator_var():
    capp = ""
    
    for sourceNode in X:
        for destNode in Z:
            equation = ""
            for transitNode in Y:
                equation += ("u{}{}{} + ".format(sourceNode, transitNode, destNode))

            equation = equation[:-2] + "= 2" + "\n" 
            capp += equation

    capp += "\n"
    return capp



def path_flow_constraint():
    capp = ""
    
    for sourceNode in X:
        for destNode in Z:
            for transitNode in Y:
                equation = ""
                h_ij = sourceNode + destNode
                equation += ("2 x{}{}{} - ".format(sourceNode, transitNode, destNode))
                equation += ("{} u{}{}{} <= 0\n".format(h_ij, sourceNode, transitNode, destNode))

                capp += equation

    capp += "\n"
    return capp



def bounds():
    bounds = ""

    for sourceNode in X:
        for transitNode in Y:
            i = sourceNode
            k = transitNode
            C_ik = "c" + str(i) + str(k)
            
            bounds += (C_ik + ">=0" + "\n" )


    for transitNode in Y:
        for destNode in Z:
            k = transitNode
            j = destNode
            D_kj = "d" + str(k) + str(j)
            
            bounds += (D_kj + ">=0" + "\n")


    for sourceNode in X:
        for destNode in Z:
            for transitNode in Y:
                equation = ("x{}{}{} >= 0".format(sourceNode, transitNode, destNode))
                bounds += (equation + "\n")

    return bounds



def create_lp_file(text):
    file = open("737.lp", 'w')
    file.write(text)
    file.close


    
def main():  
    demand_volume = demand_volumes_constraint()
    ST_capacity = ST_capacity_constraint()
    TD_capacity = TD_capacity_constraint()
    indicator = indicator_var()
    path_flow = path_flow_constraint()
    bound = bounds()
    
    text = (demand_volumes + ST_capacity + TD_capacity +
                indicator_var + path_flow + bounds)
    
    create_lp_file(text)

    
main()
