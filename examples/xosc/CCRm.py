from scenariogeneration import xosc, prettyprint
import os

## example of parametrized EUNCAP2020 CCRm case

ttc_at_speed = 5
acceleration_time = 5

def CCRm(ego_speedvalue,offset):

    # create empty catalog
    catalog = xosc.Catalog()

    # add straight road
    road = xosc.RoadNetwork(roadfile='../xodr/straight_500m.xodr',scenegraph='../models/straight_500m.osgb')

    # create empty paramdeclaration
    paramdec = xosc.ParameterDeclarations()

    egoname = 'Ego'
    targetname = 'Target1'

    ### create vehicles
    ego_width = 2
    target_width = 1.8

    bb = xosc.BoundingBox(ego_width,5,1.8,2.0,0,0.9)
    fa = xosc.Axle(0.523598775598,0.8,1.68,2.98,0.4)
    ba = xosc.Axle(0.523598775598,0.8,1.68,0,0.4)
    white_veh = xosc.Vehicle('car_white',xosc.VehicleCategory.car,bb,fa,ba,69,10,10)

    white_veh.add_property_file('../models/car_white.osgb')
    white_veh.add_property('model_id','0')

    bb = xosc.BoundingBox(target_width,4.5,1.5,1.3,0,0.8)
    fa = xosc.Axle(0.523598775598,0.8,1.68,2.98,0.4)
    ba = xosc.Axle(0.523598775598,0.8,1.68,0,0.4)
    red_veh = xosc.Vehicle('car_red',xosc.VehicleCategory.car,bb,fa,ba,69,10,10)

    red_veh.add_property_file('../models/car_red.osgb')
    red_veh.add_property('model_id','2')

    ## create entities
    entities = xosc.Entities()
    entities.add_scenario_object(egoname,white_veh)
    entities.add_scenario_object(targetname,red_veh)


    # create init (0 starting speed)
    init = xosc.Init()
    step_time = xosc.TransitionDynamics(xosc.DynamicsShapes.step,xosc.DynamicsDimension.time,1)
    
    # caluclate correct offset based on target vehicle width
    cal_offset = offset/100*target_width

    egospeed = xosc.AbsoluteSpeedAction(0,step_time)
    egostart = xosc.TeleportAction(xosc.LanePosition(25,cal_offset,-1,1))


    startpos = 25 + (ego_speedvalue-20)/3.6* (acceleration_time+ttc_at_speed)

    targetspeed = xosc.AbsoluteSpeedAction(0,step_time)
    targetstart = xosc.TeleportAction(xosc.LanePosition(startpos,0,-1,1))

    init.add_init_action(egoname,egospeed)
    init.add_init_action(egoname,egostart)
    init.add_init_action(targetname,targetspeed)
    init.add_init_action(targetname,targetstart)

    # create start trigger
    trigger = xosc.ValueTrigger('starttrigger',0,xosc.ConditionEdge.rising,xosc.SimulationTimeCondition(1,xosc.Rule.greaterThan))

    # accelerate cars to wanted velocity
    eventego = xosc.Event('egospeedchange',xosc.Priority.overwrite)
    eventego.add_trigger(trigger)

    ego_action = xosc.AbsoluteSpeedAction(ego_speedvalue/3.6,xosc.TransitionDynamics(xosc.DynamicsShapes.linear,xosc.DynamicsDimension.time,acceleration_time))
    eventego.add_action('newspeed',ego_action)

    event_tar = xosc.Event('targetspeedchange',xosc.Priority.overwrite)
    event_tar.add_trigger(trigger)

    target_action = xosc.AbsoluteSpeedAction(20/3.6,xosc.TransitionDynamics(xosc.DynamicsShapes.linear,xosc.DynamicsDimension.time,acceleration_time))
    event_tar.add_action('targetspeed',target_action)

    # create maneuvers/maneuvergroups
    ego_man = xosc.Maneuver('ego man')
    ego_man.add_event(eventego)

    tar_man = xosc.Maneuver('target man')
    tar_man.add_event(event_tar)

    egomangr = xosc.ManeuverGroup('egomangr')
    egomangr.add_actor(egoname)
    egomangr.add_maneuver(ego_man)

    tarmangr = xosc.ManeuverGroup('tarmangr')
    tarmangr.add_actor(targetname)
    tarmangr.add_maneuver(tar_man)

    # create act 
    act = xosc.Act('ccrm act',xosc.ValueTrigger('starttrigger',0,xosc.ConditionEdge.rising,xosc.SimulationTimeCondition(0,xosc.Rule.greaterThan)))

    act.add_maneuver_group(egomangr)
    act.add_maneuver_group(tarmangr)

    # create story
    story = xosc.Story('mystory')
    story.add_act(act)

    ## create the storyboard
    sb = xosc.StoryBoard(init,xosc.ValueTrigger('stop_simulation',0,xosc.ConditionEdge.rising,xosc.SimulationTimeCondition(ttc_at_speed*2+acceleration_time,xosc.Rule.greaterThan),'stop'))
    sb.add_story(story)

    ## create and return the scenario
    sce = xosc.Scenario('CCRm_v: ' +str(ego_speedvalue) + ', offset: ' + str(offset),'Mandolin',paramdec,entities=entities,storyboard = sb,roadnetwork=road,catalog=catalog)
    return sce

if __name__ == '__main__':
    all_egospeeds = [x for x in range(30,85,5)]
    all_offsets = [-50, -25, 0, 25, 50]
    sce = CCRm(all_egospeeds[-1],all_offsets[1])
    
    # Print the resulting xml
    prettyprint(sce.get_element())

    # write the OpenSCENARIO file as xosc using current script name
    sce.write_xml(os.path.basename(__file__).replace('.py','.xosc'))

    # uncomment the following lines to display the scenario using esmini
    # from scenariogeneration import esmini
    # esmini(sce,os.path.join('esmini'))
